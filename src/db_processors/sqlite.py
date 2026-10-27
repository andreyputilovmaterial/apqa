
import datetime
import json
import sqlite3
import threading
from pathlib import Path

from .dbfile_base import DBFile as DBFileBase
from .group_base import Group
from .ids import ensure_unique, unique_slug
from .rule_base import Rule


class _RuleEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
            return obj.isoformat()
        return super().default(obj)


def _dumps(value):
    return json.dumps(value, ensure_ascii=False, cls=_RuleEncoder)


def _loads(text, default):
    if not text:
        return default
    try:
        return json.loads(text)
    except (TypeError, ValueError):
        return default


# DDL shared by schema creation (fresh databases) and the legacy migrations
# that rebuild a table in place. Keeping a single source of truth avoids the
# two copies drifting apart.
_CREATE_RULES_SQL = '''
CREATE TABLE IF NOT EXISTS rules (
    id      TEXT PRIMARY KEY,
    name    TEXT NOT NULL DEFAULT '',
    "group" TEXT NOT NULL DEFAULT '',
    meta    TEXT NOT NULL DEFAULT '{}',
    "left"  TEXT NOT NULL DEFAULT '[]',
    op      TEXT NOT NULL DEFAULT '',
    op_args TEXT NOT NULL DEFAULT '{}',
    "right" TEXT NOT NULL DEFAULT '[]'
)
'''

_CREATE_GROUPS_SQL = '''
CREATE TABLE IF NOT EXISTS groups (
    id      TEXT PRIMARY KEY,
    name    TEXT NOT NULL DEFAULT '',
    parent  TEXT NOT NULL DEFAULT '',
    aliases TEXT NOT NULL DEFAULT '[]',
    meta    TEXT NOT NULL DEFAULT '{}'
)
'''


@DBFileBase.register('sqlite')
class DBFileSqlite(DBFileBase):
    """SQLite-backed QC-rules database.

    The rule is stored one-per-row, mirroring the rule shape from
    :class:`~.rule_base.Rule`:

    - ``id``       (TEXT PRIMARY KEY)  — technical id (auto-generated slug)
    - ``name``     (TEXT)              — display name
    - ``"group"``  (TEXT)              — id of the owning group ('' = ungrouped)
    - ``meta``     (JSON text)
    - ``"left"``   (JSON text)
    - ``op``       (TEXT)
    - ``op_args``  (JSON text)
    - ``"right"``  (JSON text)

    ``meta``, ``"left"``, ``op_args`` and ``"right"`` are serialized as JSON;
    ``op`` is a plain text name. ``"left"``/``"right"``/``"group"`` are quoted
    because they are SQL keywords.

    Date/time values inside the JSON columns are serialized to ISO-8601 strings
    (JSON has no native date type), so ``meta`` entries like ``created_at``
    round-trip as text.
    """

    def __init__(self, resource_path):
        self.resource_path = Path(resource_path).resolve()
        if not self.resource_path.is_file():
            raise FileNotFoundError(f'db file: file not found: {self.resource_path}')

        # The webserver handles requests in worker threads, but keeps a single
        # DBFile instance. We share one connection across threads and guard it
        # with a re-entrant lock.
        self._conn = sqlite3.connect(
            str(self.resource_path),
            check_same_thread=False,
        )
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.RLock()
        self._ensure_schema()

    def _columns(self, table):
        return [
            row['name']
            for row in self._conn.execute(f'PRAGMA table_info({table})').fetchall()
        ]

    def _ensure_schema(self):
        with self._lock:
            # Create the tables in their current (id/name) shape when the file is new.
            self._conn.execute(_CREATE_RULES_SQL)
            self._conn.execute(_CREATE_GROUPS_SQL)
            # Bring databases created before the id/name split up to date. Groups
            # go first so the rules migration can remap old `group` references.
            self._migrate_groups_to_id()
            self._migrate_rules_to_id()
            # The old project-level `definitions` table is obsolete (aliases now
            # live on groups). Drop it — no backward compatibility maintained.
            self._conn.execute('DROP TABLE IF EXISTS definitions')
            self._conn.commit()

    @classmethod
    def _init_storage(cls, resource_path):
        path = Path(resource_path).resolve()
        if path.exists():
            raise FileExistsError(f'db file: already exists: {path}')
        conn = sqlite3.connect(str(path))
        try:
            conn.execute(_CREATE_RULES_SQL)
            conn.execute(_CREATE_GROUPS_SQL)
            conn.commit()
        finally:
            conn.close()
        return path

    def _migrate_groups_to_id(self):
        columns = self._columns('groups')
        if 'id' in columns:
            return
        if 'aliases' not in columns:
            self._conn.execute(
                'ALTER TABLE groups ADD COLUMN aliases TEXT NOT NULL DEFAULT \'[]\''
            )
        rows = self._conn.execute(
            'SELECT name, parent, aliases, meta FROM groups ORDER BY rowid'
        ).fetchall()
        name_to_id = {}
        for row in rows:
            gid = unique_slug(row['name'], set(name_to_id.values()), fallback='group')
            name_to_id[row['name']] = gid
        self._conn.execute('ALTER TABLE groups RENAME TO groups_old')
        self._conn.execute(_CREATE_GROUPS_SQL)
        for row in rows:
            gid = name_to_id[row['name']]
            parent = name_to_id.get(row['parent'], row['parent']) if row['parent'] else ''
            self._conn.execute(
                'INSERT INTO groups (id, name, parent, aliases, meta) VALUES (?, ?, ?, ?, ?)',
                (gid, row['name'], parent, row['aliases'], row['meta']),
            )
        self._conn.execute('DROP TABLE groups_old')

    def _migrate_rules_to_id(self):
        columns = self._columns('rules')
        if 'id' in columns:
            return
        if 'op_args' not in columns:
            self._conn.execute(
                'ALTER TABLE rules ADD COLUMN op_args TEXT NOT NULL DEFAULT \'{}\''
            )
        if 'group' not in columns:
            self._conn.execute(
                'ALTER TABLE rules ADD COLUMN "group" TEXT NOT NULL DEFAULT \'\''
            )
        # Group display name -> id, to remap old `rule.group` references.
        name_to_id = {
            row['name']: row['id']
            for row in self._conn.execute('SELECT id, name FROM groups').fetchall()
        }
        rows = self._conn.execute(
            'SELECT name, "group", meta, "left", op, op_args, "right" FROM rules ORDER BY rowid'
        ).fetchall()
        rule_name_to_id = {}
        for row in rows:
            rid = unique_slug(row['name'], set(rule_name_to_id.values()), fallback='rule')
            rule_name_to_id[row['name']] = rid
        self._conn.execute('ALTER TABLE rules RENAME TO rules_old')
        self._conn.execute(_CREATE_RULES_SQL)
        for row in rows:
            rid = rule_name_to_id[row['name']]
            group = name_to_id.get(row['group'], row['group']) if row['group'] else ''
            self._conn.execute(
                'INSERT INTO rules (id, name, "group", meta, "left", op, op_args, "right") '
                'VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                (
                    rid,
                    row['name'],
                    group,
                    row['meta'],
                    row['left'],
                    row['op'],
                    row['op_args'],
                    row['right'],
                ),
            )
        self._conn.execute('DROP TABLE rules_old')


    def save(self):
        with self._lock:
            self._conn.commit()

    # ---- CRUD -------------------------------------------------------------

    def list_rules(self):
        with self._lock:
            rows = self._conn.execute(
                'SELECT * FROM rules ORDER BY rowid'
            ).fetchall()
        return [self._row_to_rule(row) for row in rows]

    def get_rule(self, rule_id):
        rule_id = f'{rule_id}'
        with self._lock:
            row = self._conn.execute(
                'SELECT * FROM rules WHERE id = ?', (rule_id,)
            ).fetchone()
        if row is None:
            raise KeyError(f'rule not found: {rule_id}')
        return self._row_to_rule(row)

    def has_rule(self, rule_id):
        rule_id = f'{rule_id}'
        with self._lock:
            row = self._conn.execute(
                'SELECT 1 FROM rules WHERE id = ?', (rule_id,)
            ).fetchone()
        return row is not None

    def add_rule(self, rule):
        if not isinstance(rule, Rule):
            rule = Rule.from_dict(rule)
        rule.id = ensure_unique(rule.id, self._existing_rule_ids())
        rule.group = self.resolve_group_ref(rule.group)
        with self._lock:
            self._conn.execute(
                'INSERT INTO rules (id, name, "group", meta, "left", op, op_args, "right") '
                'VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                (
                    rule.id,
                    rule.name,
                    rule.group,
                    _dumps(rule.meta),
                    _dumps(rule.left),
                    rule.op,
                    _dumps(rule.op_args),
                    _dumps(rule.right),
                ),
            )
            self._conn.commit()
        return rule

    def update_rule(self, rule_id, **changes):
        # note: `rule_id` cannot be passed as a keyword here (Python raises
        # TypeError) — a rule's id is stable and cannot be changed.
        if 'id' in changes:
            raise ValueError("a rule's id cannot be changed")
        rule_id = f'{rule_id}'
        rule = self.get_rule(rule_id)
        rule.update(**changes)
        rule.group = self.resolve_group_ref(rule.group)
        with self._lock:
            self._conn.execute(
                'UPDATE rules SET name = ?, "group" = ?, meta = ?, "left" = ?, op = ?, op_args = ?, "right" = ? '
                'WHERE id = ?',
                (
                    rule.name,
                    rule.group,
                    _dumps(rule.meta),
                    _dumps(rule.left),
                    rule.op,
                    _dumps(rule.op_args),
                    _dumps(rule.right),
                    rule_id,
                ),
            )
            self._conn.commit()
        return rule

    def rename_rule(self, rule_id, new_name):
        rule_id = f'{rule_id}'
        rule = self.get_rule(rule_id)
        rule.name = f'{new_name}'
        with self._lock:
            self._conn.execute(
                'UPDATE rules SET name = ? WHERE id = ?', (rule.name, rule_id)
            )
            self._conn.commit()
        return rule

    def delete_rule(self, rule_id):
        rule_id = f'{rule_id}'
        rule = self.get_rule(rule_id)
        with self._lock:
            self._conn.execute('DELETE FROM rules WHERE id = ?', (rule_id,))
            self._conn.commit()
        return rule

    # ---- groups CRUD ---------------------------------------------------------

    def list_groups(self):
        with self._lock:
            rows = self._conn.execute(
                'SELECT * FROM groups ORDER BY rowid'
            ).fetchall()
        return [self._row_to_group(row) for row in rows]

    def get_group(self, group_id):
        group_id = f'{group_id}'
        with self._lock:
            row = self._conn.execute(
                'SELECT * FROM groups WHERE id = ?', (group_id,)
            ).fetchone()
        if row is None:
            raise KeyError(f'group not found: {group_id}')
        return self._row_to_group(row)

    def has_group(self, group_id):
        group_id = f'{group_id}'
        with self._lock:
            row = self._conn.execute(
                'SELECT 1 FROM groups WHERE id = ?', (group_id,)
            ).fetchone()
        return row is not None

    def add_group(self, group):
        if not isinstance(group, Group):
            group = Group.from_dict(group)
        group.id = ensure_unique(group.id, self._existing_group_ids())
        group.parent = self._validate_group_parent(group, group.parent)
        with self._lock:
            self._conn.execute(
                'INSERT INTO groups (id, name, parent, aliases, meta) VALUES (?, ?, ?, ?, ?)',
                (group.id, group.name, group.parent, _dumps(group.aliases), _dumps(group.meta)),
            )
            self._conn.commit()
        return group

    def update_group(self, group_id, **changes):
        # note: `group_id` cannot be passed as a keyword here (Python raises
        # TypeError) — a group's id is stable and cannot be changed.
        if 'id' in changes:
            raise ValueError("a group's id cannot be changed")
        group_id = f'{group_id}'
        group = self.get_group(group_id)
        group.update(**changes)
        group.parent = self._validate_group_parent(group, group.parent)
        with self._lock:
            self._conn.execute(
                'UPDATE groups SET name = ?, parent = ?, aliases = ?, meta = ? WHERE id = ?',
                (group.name, group.parent, _dumps(group.aliases), _dumps(group.meta), group_id),
            )
            self._conn.commit()
        return group

    def rename_group(self, group_id, new_name):
        group_id = f'{group_id}'
        group = self.get_group(group_id)
        group.name = f'{new_name}'
        with self._lock:
            self._conn.execute(
                'UPDATE groups SET name = ? WHERE id = ?', (group.name, group_id)
            )
            self._conn.commit()
        return group

    def delete_group(self, group_id):
        group_id = f'{group_id}'
        group = self.get_group(group_id)
        with self._lock:
            child = self._conn.execute(
                'SELECT 1 FROM groups WHERE parent = ?', (group_id,)
            ).fetchone()
            rule = self._conn.execute(
                'SELECT 1 FROM rules WHERE "group" = ?', (group_id,)
            ).fetchone()
            if child is not None:
                raise ValueError(f'group is not empty (it has sub-groups): {group_id}')
            if rule is not None:
                raise ValueError(f'group is not empty (it has rules): {group_id}')
            self._conn.execute('DELETE FROM groups WHERE id = ?', (group_id,))
            self._conn.commit()
        return group

    # ---- helpers ----------------------------------------------------------

    def _row_to_rule(self, row):
        return Rule.from_dict({
            'id': row['id'],
            'name': row['name'],
            'group': row['group'],
            'meta': _loads(row['meta'], {}),
            'left': _loads(row['left'], []),
            'op': row['op'],
            'op_args': _loads(row['op_args'], {}),
            'right': _loads(row['right'], []),
        })

    def _row_to_group(self, row):
        return Group.from_dict({
            'id': row['id'],
            'name': row['name'],
            'parent': row['parent'],
            'aliases': _loads(row['aliases'], []),
            'meta': _loads(row['meta'], {}),
        })

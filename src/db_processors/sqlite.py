
import datetime
import json
import sqlite3
import threading
from pathlib import Path

from .dbfile_base import DBFile as DBFileBase
from .group_base import Group
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


@DBFileBase.register('sqlite')
class DBFileSqlite(DBFileBase):
    """SQLite-backed QC-rules database.

    The rule is stored one-per-row, mirroring the rule shape from
    :class:`~.rule_base.Rule`:

    - ``name``     (TEXT PRIMARY KEY)
    - ``"group"``  (TEXT)
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

    def _ensure_schema(self):
        with self._lock:
            self._conn.execute(
                '''
                CREATE TABLE IF NOT EXISTS rules (
                    name    TEXT PRIMARY KEY,
                    "group" TEXT NOT NULL DEFAULT '',
                    meta    TEXT NOT NULL DEFAULT '{}',
                    "left"  TEXT NOT NULL DEFAULT '[]',
                    op      TEXT NOT NULL DEFAULT '',
                    op_args TEXT NOT NULL DEFAULT '{}',
                    "right" TEXT NOT NULL DEFAULT '[]'
                )
                '''
            )
            # Migrate databases created before ``op_args``/``"group"`` existed.
            columns = [
                row['name']
                for row in self._conn.execute('PRAGMA table_info(rules)').fetchall()
            ]
            if 'op_args' not in columns:
                self._conn.execute(
                    'ALTER TABLE rules ADD COLUMN op_args TEXT NOT NULL DEFAULT \'{}\''
                )
            if 'group' not in columns:
                self._conn.execute(
                    'ALTER TABLE rules ADD COLUMN "group" TEXT NOT NULL DEFAULT \'\''
                )
            self._conn.execute(
                '''
                CREATE TABLE IF NOT EXISTS groups (
                    name    TEXT PRIMARY KEY,
                    parent  TEXT NOT NULL DEFAULT '',
                    aliases TEXT NOT NULL DEFAULT '[]',
                    meta    TEXT NOT NULL DEFAULT '{}'
                )
                '''
            )
            # Migrate databases created before ``aliases`` existed on groups.
            group_columns = [
                row['name']
                for row in self._conn.execute('PRAGMA table_info(groups)').fetchall()
            ]
            if 'aliases' not in group_columns:
                self._conn.execute(
                    'ALTER TABLE groups ADD COLUMN aliases TEXT NOT NULL DEFAULT \'[]\''
                )
            # The old project-level `definitions` table is obsolete (aliases now
            # live on groups). Drop it — no backward compatibility maintained.
            self._conn.execute('DROP TABLE IF EXISTS definitions')
            self._conn.commit()

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

    def get_rule(self, name):
        name = f'{name}'
        with self._lock:
            row = self._conn.execute(
                'SELECT * FROM rules WHERE name = ?', (name,)
            ).fetchone()
        if row is None:
            raise KeyError(f'rule not found: {name}')
        return self._row_to_rule(row)

    def has_rule(self, name):
        name = f'{name}'
        with self._lock:
            row = self._conn.execute(
                'SELECT 1 FROM rules WHERE name = ?', (name,)
            ).fetchone()
        return row is not None

    def add_rule(self, rule):
        if not isinstance(rule, Rule):
            rule = Rule.from_dict(rule)
        if self.has_rule(rule.name):
            raise ValueError(f'rule already exists: {rule.name}')
        with self._lock:
            self._conn.execute(
                'INSERT INTO rules (name, "group", meta, "left", op, op_args, "right") '
                'VALUES (?, ?, ?, ?, ?, ?, ?)',
                (
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

    def update_rule(self, name, **changes):
        # note: `name` cannot be passed as a keyword here (Python raises
        # TypeError) — renames go through rename_rule().
        name = f'{name}'
        rule = self.get_rule(name)
        rule.update(**changes)
        with self._lock:
            self._conn.execute(
                'UPDATE rules SET "group" = ?, meta = ?, "left" = ?, op = ?, op_args = ?, "right" = ? '
                'WHERE name = ?',
                (
                    rule.group,
                    _dumps(rule.meta),
                    _dumps(rule.left),
                    rule.op,
                    _dumps(rule.op_args),
                    _dumps(rule.right),
                    name,
                ),
            )
            self._conn.commit()
        return rule

    def rename_rule(self, name, new_name):
        name = f'{name}'
        rule = self.get_rule(name)
        new_name = f'{new_name}'
        if new_name == name:
            return rule
        if self.has_rule(new_name):
            raise ValueError(f'rule already exists: {new_name}')
        with self._lock:
            self._conn.execute(
                'UPDATE rules SET name = ? WHERE name = ?', (new_name, name)
            )
            self._conn.commit()
        rule.name = new_name
        return rule

    def delete_rule(self, name):
        name = f'{name}'
        rule = self.get_rule(name)
        with self._lock:
            self._conn.execute('DELETE FROM rules WHERE name = ?', (name,))
            self._conn.commit()
        return rule

    # ---- groups CRUD ---------------------------------------------------------

    def list_groups(self):
        with self._lock:
            rows = self._conn.execute(
                'SELECT * FROM groups ORDER BY rowid'
            ).fetchall()
        return [self._row_to_group(row) for row in rows]

    def get_group(self, name):
        name = f'{name}'
        with self._lock:
            row = self._conn.execute(
                'SELECT * FROM groups WHERE name = ?', (name,)
            ).fetchone()
        if row is None:
            raise KeyError(f'group not found: {name}')
        return self._row_to_group(row)

    def has_group(self, name):
        name = f'{name}'
        with self._lock:
            row = self._conn.execute(
                'SELECT 1 FROM groups WHERE name = ?', (name,)
            ).fetchone()
        return row is not None

    def add_group(self, group):
        if not isinstance(group, Group):
            group = Group.from_dict(group)
        if self.has_group(group.name):
            raise ValueError(f'group already exists: {group.name}')
        group.parent = self._validate_group_parent(group.name, group.parent)
        with self._lock:
            self._conn.execute(
                'INSERT INTO groups (name, parent, aliases, meta) VALUES (?, ?, ?, ?)',
                (group.name, group.parent, _dumps(group.aliases), _dumps(group.meta)),
            )
            self._conn.commit()
        return group

    def update_group(self, name, **changes):
        # note: `name` cannot be passed as a keyword here (Python raises
        # TypeError) — renames go through rename_group().
        name = f'{name}'
        group = self.get_group(name)
        group.update(**changes)
        group.parent = self._validate_group_parent(name, group.parent)
        with self._lock:
            self._conn.execute(
                'UPDATE groups SET parent = ?, aliases = ?, meta = ? WHERE name = ?',
                (group.parent, _dumps(group.aliases), _dumps(group.meta), name),
            )
            self._conn.commit()
        return group

    def rename_group(self, name, new_name):
        name = f'{name}'
        group = self.get_group(name)
        new_name = f'{new_name}'
        if new_name == name:
            return group
        if self.has_group(new_name):
            raise ValueError(f'group already exists: {new_name}')
        with self._lock:
            self._conn.execute(
                'UPDATE groups SET name = ? WHERE name = ?', (new_name, name)
            )
            self._conn.execute(
                'UPDATE groups SET parent = ? WHERE parent = ?', (new_name, name)
            )
            self._conn.execute(
                'UPDATE rules SET "group" = ? WHERE "group" = ?', (new_name, name)
            )
            self._conn.commit()
        group.name = new_name
        return group

    def delete_group(self, name):
        name = f'{name}'
        group = self.get_group(name)
        with self._lock:
            child = self._conn.execute(
                'SELECT 1 FROM groups WHERE parent = ?', (name,)
            ).fetchone()
            rule = self._conn.execute(
                'SELECT 1 FROM rules WHERE "group" = ?', (name,)
            ).fetchone()
            if child is not None:
                raise ValueError(f'group is not empty (it has sub-groups): {name}')
            if rule is not None:
                raise ValueError(f'group is not empty (it has rules): {name}')
            self._conn.execute('DELETE FROM groups WHERE name = ?', (name,))
            self._conn.commit()
        return group

    # ---- helpers ----------------------------------------------------------

    def _row_to_rule(self, row):
        return Rule.from_dict({
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
            'name': row['name'],
            'parent': row['parent'],
            'aliases': _loads(row['aliases'], []),
            'meta': _loads(row['meta'], {}),
        })


import json
import sqlite3
import threading
from pathlib import Path

from .dbfile_base import DBFile as DBFileBase
from .rule_base import Rule


def _dumps(value):
    return json.dumps(value, ensure_ascii=False)


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

    - ``name``   (TEXT PRIMARY KEY)
    - ``meta``   (JSON text)
    - ``"left"``  (JSON text)
    - ``op``     (TEXT)
    - ``"right"`` (JSON text)

    ``meta``, ``"left"`` and ``"right"`` are serialized as JSON; ``op`` is a
    plain text name. ``"left"``/``"right"`` are quoted because they are SQL
    keywords.
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
                    name   TEXT PRIMARY KEY,
                    meta   TEXT NOT NULL DEFAULT '{}',
                    "left"  TEXT NOT NULL DEFAULT '[]',
                    op     TEXT NOT NULL DEFAULT '',
                    "right" TEXT NOT NULL DEFAULT '[]'
                )
                '''
            )
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
                'INSERT INTO rules (name, meta, "left", op, "right") '
                'VALUES (?, ?, ?, ?, ?)',
                (
                    rule.name,
                    _dumps(rule.meta),
                    _dumps(rule.left),
                    rule.op,
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
                'UPDATE rules SET meta = ?, "left" = ?, op = ?, "right" = ? '
                'WHERE name = ?',
                (
                    _dumps(rule.meta),
                    _dumps(rule.left),
                    rule.op,
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

    # ---- helpers ----------------------------------------------------------

    def _row_to_rule(self, row):
        return Rule.from_dict({
            'name': row['name'],
            'meta': _loads(row['meta'], {}),
            'left': _loads(row['left'], []),
            'op': row['op'],
            'right': _loads(row['right'], []),
        })

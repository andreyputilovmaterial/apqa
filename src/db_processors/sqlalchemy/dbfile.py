"""SQLAlchemy-backed QC-rules database.

One processor for the whole family of SQL databases SQLAlchemy understands:
PostgreSQL, MySQL/MariaDB, Microsoft SQL Server (via ODBC/OLEDB drivers),
Oracle, and SQLite — selected by a SQLAlchemy URL
(``postgresql+psycopg2://user:pass@host/db``, ``mssql+pyodbc://...``, …).

The schema mirrors the SQLite backend (``rules``, ``groups``, ``project``
tables) but is described with portable SQLAlchemy Core types, so the same CRUD
contract works across every dialect. Reserved-word column names (``group``,
``left``, ``right``) are forced to be quoted, matching the SQLite schema and
avoiding dialect-specific keyword clashes.

Dialect drivers are optional: SQLAlchemy reports a missing driver (or an unknown
URL scheme) when the engine is created, and we wrap that in a readable error.
The installable optional drivers live in
``src/db_processors/sqlalchemy/requirements.txt`` and are installed best-effort
by ``run_init``.

Credentials embedded in the URL stay in the engine, but the stored
``resource_path`` (served as ``config['db_file']``, the page header, and
``GET /qc/project``) is rendered with the password hidden
(``URL.render_as_string(hide_password=True)``), so secrets never leak into the
served configuration or the UI.
"""

import datetime
import json
import threading
from pathlib import Path

from ..dbfile_base import DBFile as DBFileBase
from ..group_base import Group
from ..ids import ensure_unique
from ..project_base import Project
from ..rule_base import Rule


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


class _SQLAlchemySchema:
    """SQLAlchemy's own namespace plus the shared schema, built lazily.

    SQLAlchemy is the heaviest dependency of the db processors, and its schema
    objects (``MetaData`` and the ``rules``/``groups``/``project`` tables) are
    only needed when a SQLAlchemy URL is actually opened. Building them here —
    instead of at import time — keeps importing this module (to register the
    processor) cheap, so a YAML- or SQLite-backed session never pays for
    SQLAlchemy.
    """

    def __init__(self):
        from sqlalchemy import (
            Column,
            Integer,
            MetaData,
            String,
            Table,
            Text,
            create_engine,
            func,
            inspect,
            select,
        )
        from sqlalchemy.engine import make_url
        from sqlalchemy.sql import quoted_name

        self.make_url = make_url
        self.create_engine = create_engine
        self.inspect = inspect
        self.select = select
        self.func = func

        # Reserved-word column names are quoted everywhere, mirroring the SQLite
        # schema.
        group = quoted_name('group', True)
        left = quoted_name('left', True)
        right = quoted_name('right', True)

        metadata = MetaData()
        self.metadata = metadata
        self.rules = Table(
            'rules', metadata,
            Column('id', String(255), primary_key=True),
            Column('name', Text, nullable=False),
            Column(group, String(255), nullable=False),
            Column('meta', Text, nullable=False),
            Column(left, Text, nullable=False),
            Column('op', String(255), nullable=False),
            Column('op_args', Text, nullable=False),
            Column(right, Text, nullable=False),
            # Insertion-order marker. The hand-written SQLite backend uses `rowid`
            # for this; here it is an explicit column so ordering works on every
            # dialect.
            Column('seq', Integer, nullable=False),
        )
        self.groups = Table(
            'groups', metadata,
            Column('id', String(255), primary_key=True),
            Column('name', Text, nullable=False),
            Column('parent', String(255), nullable=False),
            Column('aliases', Text, nullable=False),
            Column('meta', Text, nullable=False),
            Column('seq', Integer, nullable=False),
        )
        self.project = Table(
            'project', metadata,
            Column('id', Integer, primary_key=True),
            Column('name', Text, nullable=False),
            Column('comment', Text, nullable=False),
            Column('meta', Text, nullable=False),
        )


_schema_cache = None
_schema_lock = threading.Lock()


def _schema():
    """Return the shared SQLAlchemy schema, importing SQLAlchemy on first use."""
    global _schema_cache
    if _schema_cache is None:
        with _schema_lock:
            if _schema_cache is None:
                _schema_cache = _SQLAlchemySchema()
    return _schema_cache


def _url(resource_path):
    """Parse ``resource_path`` into a SQLAlchemy URL or raise a readable error."""
    try:
        return _schema().make_url(f'{resource_path}')
    except Exception as error:
        raise ValueError(
            f'db file: not a valid SQLAlchemy URL: {resource_path!r}'
        ) from error


def _engine(url):
    """Create an engine for ``url``, turning URL/driver errors into ``ValueError``."""
    try:
        return _schema().create_engine(url)
    except Exception as error:
        raise ValueError(
            'db file: cannot create SQLAlchemy engine for '
            f'{url.render_as_string(hide_password=True)!r}: {error}'
        ) from error


def _is_sqlite_file_url(url):
    return url.get_backend_name() == 'sqlite' and url.database not in (None, '', ':memory:')


def _storage_exists(engine, url):
    """Return True when the storage (file or ``rules`` table) already exists."""
    if _is_sqlite_file_url(url):
        return Path(url.database).resolve().exists()
    return 'rules' in _schema().inspect(engine).get_table_names()


@DBFileBase.register('sqlalchemy')
class DBFileSqlalchemy(DBFileBase):
    """QC-rules database backed by any SQL database SQLAlchemy can reach.

    The resource address is a SQLAlchemy URL. CRUD is implemented with portable
    SQLAlchemy Core expressions against the same ``rules``/``groups``/``project``
    shape as the SQLite backend, so every dialect gets identical behavior.
    """

    def __init__(self, resource_path):
        self._sa = _schema()
        url = _url(resource_path)
        self._url = url
        self.resource_path = url.render_as_string(hide_password=True)
        self._lock = threading.RLock()
        self._engine = _engine(url)
        if _is_sqlite_file_url(url):
            path = Path(url.database).resolve()
            if not path.exists():
                self._engine.dispose()
                raise FileNotFoundError(f'db file: file not found: {path}')
        self._ensure_schema()

    @classmethod
    def _init_storage(cls, resource_path):
        url = _url(resource_path)
        engine = _engine(url)
        try:
            if _storage_exists(engine, url):
                raise FileExistsError(
                    f'db file: already exists: {url.render_as_string(hide_password=True)}'
                )
            sa = _schema()
            sa.metadata.create_all(engine)
            with engine.begin() as conn:
                conn.execute(
                    sa.project.insert().values(id=1, name='', comment='', meta='{}')
                )
        finally:
            engine.dispose()
        return url.render_as_string(hide_password=True)

    def _ensure_schema(self):
        with self._lock:
            self._sa.metadata.create_all(self._engine, checkfirst=True)
            with self._engine.begin() as conn:
                row = conn.execute(
                    self._sa.select(self._sa.project.c.id).where(self._sa.project.c.id == 1)
                ).first()
                if row is None:
                    conn.execute(
                        self._sa.project.insert().values(
                            id=1, name='', comment='', meta='{}'
                        )
                    )

    def _next_seq(self, conn, table):
        return (conn.execute(self._sa.select(self._sa.func.max(table.c.seq))).scalar() or 0) + 1

    def save(self):
        # Every mutation commits its own transaction, so there is nothing left to
        # flush on an explicit save (unlike the document backends).
        return None

    # ---- rules CRUD ---------------------------------------------------------

    def list_rules(self):
        with self._lock:
            with self._engine.connect() as conn:
                rows = conn.execute(
                    self._sa.select(self._sa.rules).order_by(self._sa.rules.c.seq)
                ).mappings().all()
        return [self._row_to_rule(row) for row in rows]

    def get_rule(self, rule_id):
        rule_id = f'{rule_id}'
        with self._lock:
            with self._engine.connect() as conn:
                row = conn.execute(
                    self._sa.select(self._sa.rules).where(self._sa.rules.c.id == rule_id)
                ).mappings().first()
        if row is None:
            raise KeyError(f'rule not found: {rule_id}')
        return self._row_to_rule(row)

    def has_rule(self, rule_id):
        rule_id = f'{rule_id}'
        with self._lock:
            with self._engine.connect() as conn:
                row = conn.execute(
                    self._sa.select(self._sa.rules.c.id).where(self._sa.rules.c.id == rule_id)
                ).first()
        return row is not None

    def add_rule(self, rule):
        if not isinstance(rule, Rule):
            rule = Rule.from_dict(rule)
        self._ensure_rule_id_available(rule)
        rule.group = self.resolve_group_ref(rule.group)
        with self._lock:
            with self._engine.begin() as conn:
                seq = self._next_seq(conn, self._sa.rules)
                conn.execute(
                    self._sa.rules.insert().values(
                        id=rule.id,
                        name=rule.name,
                        group=rule.group,
                        meta=_dumps(rule.meta),
                        left=_dumps(rule.left),
                        op=rule.op,
                        op_args=_dumps(rule.op_args),
                        right=_dumps(rule.right),
                        seq=seq,
                    )
                )
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
            with self._engine.begin() as conn:
                conn.execute(
                    self._sa.rules.update()
                    .where(self._sa.rules.c.id == rule_id)
                    .values(
                        name=rule.name,
                        group=rule.group,
                        meta=_dumps(rule.meta),
                        left=_dumps(rule.left),
                        op=rule.op,
                        op_args=_dumps(rule.op_args),
                        right=_dumps(rule.right),
                    )
                )
        return rule

    def rename_rule(self, rule_id, new_name):
        rule_id = f'{rule_id}'
        rule = self.get_rule(rule_id)
        rule.name = f'{new_name}'
        with self._lock:
            with self._engine.begin() as conn:
                conn.execute(
                    self._sa.rules.update()
                    .where(self._sa.rules.c.id == rule_id)
                    .values(name=rule.name)
                )
        return rule

    def delete_rule(self, rule_id):
        rule_id = f'{rule_id}'
        rule = self.get_rule(rule_id)
        with self._lock:
            with self._engine.begin() as conn:
                conn.execute(self._sa.rules.delete().where(self._sa.rules.c.id == rule_id))
        return rule

    # ---- groups CRUD ---------------------------------------------------------

    def list_groups(self):
        with self._lock:
            with self._engine.connect() as conn:
                rows = conn.execute(
                    self._sa.select(self._sa.groups).order_by(self._sa.groups.c.seq)
                ).mappings().all()
        return [self._row_to_group(row) for row in rows]

    def get_group(self, group_id):
        group_id = f'{group_id}'
        with self._lock:
            with self._engine.connect() as conn:
                row = conn.execute(
                    self._sa.select(self._sa.groups).where(self._sa.groups.c.id == group_id)
                ).mappings().first()
        if row is None:
            raise KeyError(f'group not found: {group_id}')
        return self._row_to_group(row)

    def has_group(self, group_id):
        group_id = f'{group_id}'
        with self._lock:
            with self._engine.connect() as conn:
                row = conn.execute(
                    self._sa.select(self._sa.groups.c.id).where(self._sa.groups.c.id == group_id)
                ).first()
        return row is not None

    def add_group(self, group):
        if not isinstance(group, Group):
            group = Group.from_dict(group)
        group.id = ensure_unique(group.id, self._existing_group_ids())
        group.parent = self._validate_group_parent(group, group.parent)
        with self._lock:
            with self._engine.begin() as conn:
                seq = self._next_seq(conn, self._sa.groups)
                conn.execute(
                    self._sa.groups.insert().values(
                        id=group.id,
                        name=group.name,
                        parent=group.parent,
                        aliases=_dumps(group.aliases),
                        meta=_dumps(group.meta),
                        seq=seq,
                    )
                )
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
            with self._engine.begin() as conn:
                conn.execute(
                    self._sa.groups.update()
                    .where(self._sa.groups.c.id == group_id)
                    .values(
                        name=group.name,
                        parent=group.parent,
                        aliases=_dumps(group.aliases),
                        meta=_dumps(group.meta),
                    )
                )
        return group

    def rename_group(self, group_id, new_name):
        group_id = f'{group_id}'
        group = self.get_group(group_id)
        group.name = f'{new_name}'
        with self._lock:
            with self._engine.begin() as conn:
                conn.execute(
                    self._sa.groups.update()
                    .where(self._sa.groups.c.id == group_id)
                    .values(name=group.name)
                )
        return group

    def delete_group(self, group_id):
        group_id = f'{group_id}'
        group = self.get_group(group_id)
        with self._lock:
            with self._engine.connect() as conn:
                child = conn.execute(
                    self._sa.select(self._sa.groups.c.id).where(self._sa.groups.c.parent == group_id)
                ).first()
                rule = conn.execute(
                    self._sa.select(self._sa.rules.c.id).where(self._sa.rules.c.group == group_id)
                ).first()
                if child is not None:
                    raise ValueError(f'group is not empty (it has sub-groups): {group_id}')
                if rule is not None:
                    raise ValueError(f'group is not empty (it has rules): {group_id}')
            with self._engine.begin() as conn:
                conn.execute(self._sa.groups.delete().where(self._sa.groups.c.id == group_id))
        return group

    # ---- project CRUD ----------------------------------------------------------

    def get_project(self):
        with self._lock:
            with self._engine.connect() as conn:
                row = conn.execute(
                    self._sa.select(
                        self._sa.project.c.name,
                        self._sa.project.c.comment,
                        self._sa.project.c.meta,
                    ).where(self._sa.project.c.id == 1)
                ).mappings().first()
        if row is None:
            return Project()
        return Project.from_dict({
            'name': row['name'],
            'comment': row['comment'],
            'meta': _loads(row['meta'], {}),
        })

    def update_project(self, **changes):
        project = self.get_project()
        project.update(**changes)
        with self._lock:
            with self._engine.begin() as conn:
                conn.execute(
                    self._sa.project.update()
                    .where(self._sa.project.c.id == 1)
                    .values(
                        name=project.name,
                        comment=project.comment,
                        meta=_dumps(project.meta),
                    )
                )
        return project

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





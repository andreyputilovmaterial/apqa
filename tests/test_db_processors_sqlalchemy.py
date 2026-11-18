"""SQLAlchemy DB processor: uniform access to any SQL database URL.

The real dialects (PostgreSQL, MySQL, MSSQL/OLEDB, …) need their optional
drivers installed, so these tests exercise the processor against SQLite — the
one dialect SQLAlchemy ships with out of the box — while still going through the
generic SQLAlchemy URL path (``sqlite://``/``sqlite:///<path>``), not the
hand-written ``DBFileSqlite`` file processor.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from src.db_processors import DBFile, DBFileSqlalchemy
from src.db_processors.sqlalchemy.dbfile import _url
from src.db_processors.rule_base import Rule


def test_router_selects_sqlalchemy_for_url():
    dbfile = DBFile('sqlite://')
    assert isinstance(dbfile, DBFileSqlalchemy)
    assert dbfile.resource_path == 'sqlite://'


def test_open_in_memory_is_empty():
    dbfile = DBFile('sqlite://')
    assert len(dbfile) == 0
    assert dbfile.list_groups() == []
    assert dbfile.get_project().to_dict() == {'name': '', 'comment': '', 'meta': {}}


def test_crud_roundtrip_persists_each_mutation(tmp_path):
    url = f'sqlite:///{tmp_path / "projects.db"}'
    DBFile.init_storage(url)
    dbfile = DBFile(url)
    dbfile.add_rule({'name': 'wave counts', 'op': 'cmp-eq'})
    dbfile.add_group({'name': 'Data'})
    dbfile.update_project(name='Demo')

    # No explicit save: every mutation commits its own transaction.
    reloaded = DBFile(url)
    assert reloaded.get_project().name == 'Demo'
    assert [r.name for r in reloaded.list_rules()] == ['wave counts']
    assert [g.name for g in reloaded.list_groups()] == ['Data']


def test_list_rules_preserves_insertion_order():
    dbfile = DBFile('sqlite://')
    for name in ('first', 'second', 'third'):
        dbfile.add_rule({'name': name})
    assert [r.name for r in dbfile.list_rules()] == ['first', 'second', 'third']


def test_add_rule_duplicate_id_raises():
    dbfile = DBFile('sqlite://')
    dbfile.add_rule({'name': 'wave counts'})
    with pytest.raises(ValueError):
        dbfile.add_rule({'name': 'wave counts'})
    assert len(dbfile) == 1


def test_rule_objects_and_json_roundtrip(tmp_path):
    url = f'sqlite:///{tmp_path / "projects.db"}'
    DBFile.init_storage(url)
    dbfile = DBFile(url)
    dbfile.add_rule({
        'name': 'with-dates',
        'op': 'cmp-eq',
        'op_args': {'unordered_arrays': True},
        'left': [{'cmdlet': 'literal', 'args': {'value': [1, 2]}}],
        'right': [{'cmdlet': 'literal', 'args': {'value': [2, 1]}}],
        'meta': {'created_at': '2026-10-14T12:00:00', 'tags': ['counts']},
    })

    reloaded = DBFile(url)
    rule = reloaded.get_rule('with-dates')
    assert isinstance(rule, Rule)
    assert rule.op_args == {'unordered_arrays': True}
    assert rule.left[0]['cmdlet'] == 'literal'
    assert rule.meta['tags'] == ['counts']


def test_groups_dedup_id_and_validate_parent():
    dbfile = DBFile('sqlite://')
    first = dbfile.add_group({'name': 'Data'})
    second = dbfile.add_group({'name': 'Data'})
    assert first.id == 'data'
    assert second.id == 'data-2'
    with pytest.raises(ValueError):
        dbfile.add_group({'name': 'Orphan', 'parent': 'Nope'})


def test_group_aliases_roundtrip(tmp_path):
    url = f'sqlite:///{tmp_path / "projects.db"}'
    DBFile.init_storage(url)
    dbfile = DBFile(url)
    dbfile.add_group({
        'name': 'Data',
        'aliases': [{'name': 'survey_mdd', 'chain': [{'cmdlet': 'literal', 'args': {'value': 1}}]}],
    })

    reloaded = DBFile(url)
    aliases = reloaded.get_group('data').aliases
    assert [a['name'] for a in aliases] == ['survey_mdd']
    assert aliases[0]['chain'][0]['cmdlet'] == 'literal'


def test_init_storage_creates_schema_and_refuses_existing(tmp_path):
    url = f'sqlite:///{tmp_path / "fresh.db"}'
    created = DBFile.init_storage(url)
    assert Path(tmp_path / 'fresh.db').is_file()

    dbfile = DBFile(url)
    assert len(dbfile) == 0
    assert dbfile.get_project().to_dict() == {'name': '', 'comment': '', 'meta': {}}

    with pytest.raises(FileExistsError):
        DBFile.init_storage(url)


def test_open_missing_sqlite_file_raises(tmp_path):
    url = f'sqlite:///{tmp_path / "nope.db"}'
    with pytest.raises(FileNotFoundError):
        DBFile(url)


def test_unknown_dialect_raises_readable_valueerror():
    with pytest.raises(ValueError, match='cannot create SQLAlchemy engine'):
        DBFile('oledb://server/database')


def test_missing_driver_raises_readable_valueerror():
    # postgresql:// defaults to the psycopg driver, which is not installed here.
    with pytest.raises(ValueError, match='cannot create SQLAlchemy engine'):
        DBFile('postgresql://user:pass@localhost/db')


def test_url_password_is_hidden():
    url = _url('postgresql://user:secret@localhost:5432/db')
    rendered = url.render_as_string(hide_password=True)
    assert 'secret' not in rendered
    assert 'user' in rendered

"""Project-level metadata storage in the YAML and SQLite databases.

A QC-rules database file describes one project. Besides rules and groups, it
carries a single project record (name, comment, and an extensible meta bag).
These tests cover reading, updating and round-tripping that record in both
supported storage formats.
"""

import json
import sqlite3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from src.db_processors import DBFile
from src.db_processors.project_base import Project


# ---- shared model behavior --------------------------------------------------

def test_project_from_dict_defaults():
    assert Project.from_dict(None).to_dict() == {
        'name': '',
        'comment': '',
        'meta': {},
    }


def test_project_from_dict():
    project = Project.from_dict({
        'name': 'Disney Brand Health Study',
        'comment': 'a note',
        'meta': {'created_by': 'apqa', 'tags': ['q1']},
    })
    assert project.name == 'Disney Brand Health Study'
    assert project.comment == 'a note'
    assert project.meta == {'created_by': 'apqa', 'tags': ['q1']}


def test_project_from_dict_non_mapping():
    with pytest.raises(ValueError):
        Project.from_dict(['not', 'a', 'mapping'])


def test_project_from_dict_meta_must_be_mapping():
    with pytest.raises(ValueError):
        Project.from_dict({'name': 'x', 'meta': ['not', 'a', 'mapping']})


def test_project_update_rejects_unknown_field():
    with pytest.raises(ValueError):
        Project().update(bogus=1)


def test_project_to_dict():
    project = Project(name='x', comment='y', meta={'z': 1})
    assert project.to_dict() == {'name': 'x', 'comment': 'y', 'meta': {'z': 1}}


# ---- YAML backend -----------------------------------------------------------

YAML_WITH_PROJECT = """\
project:
  name: Disney Brand Health Study
  comment: a note about the study
  meta:
    created_by: apqa
    tags: [q1, wave69]
groups: []
rules: []
"""


@pytest.fixture
def yaml_dbfile(tmp_path):
    db_file = tmp_path / 'projects.yaml'
    db_file.write_text(YAML_WITH_PROJECT, encoding='utf-8')
    return DBFile(str(db_file))


def test_yaml_loads_project(yaml_dbfile):
    project = yaml_dbfile.get_project()
    assert isinstance(project, Project)
    assert project.name == 'Disney Brand Health Study'
    assert project.comment == 'a note about the study'
    assert project.meta == {'created_by': 'apqa', 'tags': ['q1', 'wave69']}


def test_yaml_project_accessor(yaml_dbfile):
    assert yaml_dbfile.project.name == 'Disney Brand Health Study'


def test_yaml_missing_project_defaults_empty(tmp_path):
    db_file = tmp_path / 'projects.yaml'
    db_file.write_text('rules: []\n', encoding='utf-8')
    dbfile = DBFile(str(db_file))
    assert dbfile.get_project().to_dict() == {'name': '', 'comment': '', 'meta': {}}


def test_yaml_update_project(yaml_dbfile):
    project = yaml_dbfile.update_project(name='Renamed', comment='updated')
    assert project.name == 'Renamed'
    assert project.comment == 'updated'
    assert yaml_dbfile.get_project().meta == {'created_by': 'apqa', 'tags': ['q1', 'wave69']}


def test_yaml_save_roundtrip_project(yaml_dbfile):
    yaml_dbfile.update_project(
        name='Saved',
        comment='persisted comment',
        meta={'created_by': 'apqa', 'tags': ['saved']},
    )
    yaml_dbfile.save()

    reloaded = DBFile(str(yaml_dbfile.resource_path))
    project = reloaded.get_project()
    assert project.name == 'Saved'
    assert project.comment == 'persisted comment'
    assert project.meta == {'created_by': 'apqa', 'tags': ['saved']}


# ---- SQLite backend ---------------------------------------------------------

def _insert_project(db_path, name, comment, meta):
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        'CREATE TABLE IF NOT EXISTS project ('
        'id INTEGER PRIMARY KEY, name TEXT NOT NULL DEFAULT \'\', '
        'comment TEXT NOT NULL DEFAULT \'\', meta TEXT NOT NULL DEFAULT \'{}\')'
    )
    conn.execute(
        'INSERT OR REPLACE INTO project (id, name, comment, meta) VALUES (1, ?, ?, ?)',
        (name, comment, json.dumps(meta)),
    )
    conn.commit()
    conn.close()


@pytest.fixture
def sqlite_dbfile(tmp_path):
    db_file = tmp_path / 'projects.sqlite3'
    _insert_project(
        db_file,
        'Disney Brand Health Study',
        'a note about the study',
        {'created_by': 'apqa', 'tags': ['q1', 'wave69']},
    )
    return DBFile(str(db_file))


def test_sqlite_loads_project(sqlite_dbfile):
    project = sqlite_dbfile.get_project()
    assert isinstance(project, Project)
    assert project.name == 'Disney Brand Health Study'
    assert project.comment == 'a note about the study'
    assert project.meta == {'created_by': 'apqa', 'tags': ['q1', 'wave69']}


def test_sqlite_project_accessor(sqlite_dbfile):
    assert sqlite_dbfile.project.name == 'Disney Brand Health Study'


def test_sqlite_empty_file_creates_empty_project(tmp_path):
    db_file = tmp_path / 'fresh.sqlite3'
    db_file.write_text('', encoding='utf-8')

    dbfile = DBFile(str(db_file))
    assert dbfile.get_project().to_dict() == {'name': '', 'comment': '', 'meta': {}}


def test_sqlite_update_project(sqlite_dbfile):
    project = sqlite_dbfile.update_project(name='Renamed', comment='updated')
    assert project.name == 'Renamed'
    assert project.comment == 'updated'
    assert sqlite_dbfile.get_project().meta == {'created_by': 'apqa', 'tags': ['q1', 'wave69']}


def test_sqlite_update_project_roundtrip(sqlite_dbfile):
    sqlite_dbfile.update_project(
        name='Saved',
        comment='persisted comment',
        meta={'created_by': 'apqa', 'tags': ['saved']},
    )
    sqlite_dbfile.save()

    reloaded = DBFile(str(sqlite_dbfile.resource_path))
    project = reloaded.get_project()
    assert project.name == 'Saved'
    assert project.comment == 'persisted comment'
    assert project.meta == {'created_by': 'apqa', 'tags': ['saved']}


# ---- fresh storage creation --------------------------------------------------

def test_init_yaml_seeds_empty_project(tmp_path):
    db_file = tmp_path / 'fresh.yaml'
    DBFile.init_storage(db_file)

    dbfile = DBFile(str(db_file))
    assert dbfile.get_project().to_dict() == {'name': '', 'comment': '', 'meta': {}}


def test_init_sqlite_seeds_empty_project(tmp_path):
    db_file = tmp_path / 'fresh.sqlite3'
    DBFile.init_storage(db_file)

    dbfile = DBFile(str(db_file))
    assert dbfile.get_project().to_dict() == {'name': '', 'comment': '', 'meta': {}}


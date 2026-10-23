"""CRUD tests for project-level definitions (aliases) in YAML and SQLite."""

import json
import sqlite3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from src.db_processors import DBFile
from src.db_processors.definition_base import Definition


SAMPLE_DEF = {
    "name": "PROCESSED_DATA",
    "value": "/path/to/project/p123/data/datafile.db",
    "meta": {"comment": "processed data file"},
}


# ---- YAML backend -----------------------------------------------------------

YAML_WITH_DEFINITIONS = """\
definitions:
  - name: PROCESSED_DATA
    value: /path/to/project/p123/data/datafile.db
    meta:
      comment: processed data file
rules:
  - name: wave69-counts-equal-9002
    meta:
      tags: [counts, wave69]
    left:
      - cmdlet: get-content
        args:
          path: PROCESSED_DATA
    op: eq
    right:
      - cmdlet: literal
        args:
          value: 9002
"""


@pytest.fixture
def yaml_dbfile(tmp_path):
    db_file = tmp_path / "projects.yaml"
    db_file.write_text(YAML_WITH_DEFINITIONS, encoding="utf-8")
    return DBFile(str(db_file))


def test_yaml_loads_definitions(yaml_dbfile):
    definitions = yaml_dbfile.list_definitions()
    assert [d.name for d in definitions] == ["PROCESSED_DATA"]
    assert isinstance(definitions[0], Definition)
    assert definitions[0].value == "/path/to/project/p123/data/datafile.db"
    assert definitions[0].meta["comment"] == "processed data file"


def test_yaml_loads_rules_alongside_definitions(yaml_dbfile):
    assert len(yaml_dbfile) == 1
    assert yaml_dbfile.get_rule("wave69-counts-equal-9002").left[0]["args"]["path"] == "PROCESSED_DATA"


def test_yaml_definitions_accessor(yaml_dbfile):
    assert [d.name for d in yaml_dbfile.definitions] == ["PROCESSED_DATA"]


def test_yaml_add_definition(yaml_dbfile):
    yaml_dbfile.add_definition({"name": "TITLES", "value": "/data/titles.xlsx"})
    assert yaml_dbfile.has_definition("TITLES")
    assert yaml_dbfile.get_definition("TITLES").value == "/data/titles.xlsx"


def test_yaml_add_definition_duplicate(yaml_dbfile):
    with pytest.raises(ValueError):
        yaml_dbfile.add_definition(SAMPLE_DEF)


def test_yaml_update_definition(yaml_dbfile):
    definition = yaml_dbfile.update_definition("PROCESSED_DATA", value="/data/new.db")
    assert definition.value == "/data/new.db"
    assert yaml_dbfile.get_definition("PROCESSED_DATA").value == "/data/new.db"


def test_yaml_update_definition_unknown_field(yaml_dbfile):
    with pytest.raises(ValueError):
        yaml_dbfile.update_definition("PROCESSED_DATA", bogus_field=1)


def test_yaml_rename_definition(yaml_dbfile):
    definition = yaml_dbfile.rename_definition("PROCESSED_DATA", "DATA")
    assert definition.name == "DATA"
    assert "PROCESSED_DATA" not in yaml_dbfile._definitions
    assert yaml_dbfile.has_definition("DATA")


def test_yaml_delete_definition(yaml_dbfile):
    deleted = yaml_dbfile.delete_definition("PROCESSED_DATA")
    assert deleted.name == "PROCESSED_DATA"
    assert yaml_dbfile.list_definitions() == []


def test_yaml_save_roundtrip(yaml_dbfile, tmp_path):
    yaml_dbfile.add_definition({"name": "TITLES", "value": "/data/titles.xlsx"})
    yaml_dbfile.save()

    reloaded = DBFile(str(yaml_dbfile.resource_path))
    assert [d.name for d in reloaded.list_definitions()] == ["PROCESSED_DATA", "TITLES"]


def test_yaml_backward_compatible_list_format(tmp_path):
    db_file = tmp_path / "legacy.yaml"
    db_file.write_text(
        "- name: r1\n  op: eq\n",
        encoding="utf-8",
    )
    dbfile = DBFile(str(db_file))
    assert len(dbfile) == 1
    assert dbfile.list_definitions() == []


# ---- SQLite backend ---------------------------------------------------------

def _insert_sqlite_definition(db_path, definition):
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        'CREATE TABLE IF NOT EXISTS definitions ('
        'name TEXT PRIMARY KEY, '
        'value TEXT NOT NULL DEFAULT \'\', '
        'meta TEXT NOT NULL DEFAULT \'{}\''
        ')'
    )
    conn.execute(
        'INSERT INTO definitions (name, value, meta) VALUES (?, ?, ?)',
        (definition["name"], definition["value"], json.dumps(definition.get("meta", {}))),
    )
    conn.commit()
    conn.close()


@pytest.fixture
def sqlite_dbfile(tmp_path):
    db_file = tmp_path / "projects.sqlite3"
    _insert_sqlite_definition(db_file, SAMPLE_DEF)
    return DBFile(str(db_file))


def test_sqlite_loads_definitions(sqlite_dbfile):
    definitions = sqlite_dbfile.list_definitions()
    assert [d.name for d in definitions] == ["PROCESSED_DATA"]
    assert isinstance(definitions[0], Definition)
    assert definitions[0].value == "/path/to/project/p123/data/datafile.db"


def test_sqlite_add_definition(sqlite_dbfile):
    sqlite_dbfile.add_definition({"name": "TITLES", "value": "/data/titles.xlsx"})
    assert sqlite_dbfile.has_definition("TITLES")


def test_sqlite_update_definition(sqlite_dbfile):
    definition = sqlite_dbfile.update_definition("PROCESSED_DATA", value="/data/new.db")
    assert definition.value == "/data/new.db"


def test_sqlite_rename_definition(sqlite_dbfile):
    definition = sqlite_dbfile.rename_definition("PROCESSED_DATA", "DATA")
    assert definition.name == "DATA"
    assert not sqlite_dbfile.has_definition("PROCESSED_DATA")


def test_sqlite_delete_definition(sqlite_dbfile):
    deleted = sqlite_dbfile.delete_definition("PROCESSED_DATA")
    assert deleted.name == "PROCESSED_DATA"
    assert sqlite_dbfile.list_definitions() == []


def test_sqlite_save_roundtrip(sqlite_dbfile):
    sqlite_dbfile.add_definition({"name": "TITLES", "value": "/data/titles.xlsx"})
    sqlite_dbfile.save()

    reloaded = DBFile(str(sqlite_dbfile.resource_path))
    assert [d.name for d in reloaded.list_definitions()] == ["PROCESSED_DATA", "TITLES"]


def test_sqlite_creates_definitions_table(tmp_path):
    db_file = tmp_path / "fresh.sqlite3"
    db_file.write_text("", encoding="utf-8")

    dbfile = DBFile(str(db_file))
    assert dbfile.list_definitions() == []
    dbfile.add_definition(SAMPLE_DEF)
    assert dbfile.has_definition("PROCESSED_DATA")


# ---- shared model behavior --------------------------------------------------

def test_definition_from_dict_requires_name():
    with pytest.raises(ValueError):
        Definition.from_dict({"value": "/x"})


def test_definition_from_dict_non_mapping():
    with pytest.raises(ValueError):
        Definition.from_dict(["not", "a", "mapping"])


def test_definition_to_dict_roundtrip():
    d = Definition.from_dict(SAMPLE_DEF).to_dict()
    assert d["name"] == "PROCESSED_DATA"
    assert d["value"] == "/path/to/project/p123/data/datafile.db"
    assert d["meta"]["comment"] == "processed data file"

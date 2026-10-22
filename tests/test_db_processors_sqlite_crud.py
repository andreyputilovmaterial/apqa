"""Round-trip and CRUD tests for the SQLite rules database."""

import json
import sqlite3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from src.db_processors import DBFile
from src.db_processors.rule_base import Rule


SAMPLE = {
    "name": "wave69-counts-equal-9002",
    "meta": {"enabled": True, "tags": ["counts", "wave69"], "markers": []},
    "left": [
        {"cmdlet": "get-content", "args": {"path": "/path/to/specs.sav"}},
        {"cmdlet": "count"},
    ],
    "op": "eq",
    "right": [
        {"cmdlet": "literal", "args": {"value": 9002}},
    ],
}


def _insert_raw(db_path, rule):
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        'CREATE TABLE IF NOT EXISTS rules ('
        'name TEXT PRIMARY KEY, '
        'meta TEXT NOT NULL DEFAULT \'{}\', '
        '"left" TEXT NOT NULL DEFAULT \'[]\', '
        'op TEXT NOT NULL DEFAULT \'\', '
        '"right" TEXT NOT NULL DEFAULT \'[]\''
        ')'
    )
    conn.execute(
        'INSERT INTO rules (name, meta, "left", op, "right") '
        'VALUES (?, ?, ?, ?, ?)',
        (
            rule["name"],
            json.dumps(rule["meta"]),
            json.dumps(rule["left"]),
            rule["op"],
            json.dumps(rule["right"]),
        ),
    )
    conn.commit()
    conn.close()


@pytest.fixture
def dbfile(tmp_path):
    db_file = tmp_path / "projects.sqlite3"
    _insert_raw(db_file, SAMPLE)
    return DBFile(str(db_file))


def test_load_rules(dbfile):
    assert len(dbfile) == 1
    assert "wave69-counts-equal-9002" in dbfile
    rule = dbfile.get_rule("wave69-counts-equal-9002")
    assert isinstance(rule, Rule)
    assert rule.op == "eq"
    assert rule.meta["enabled"] is True
    assert len(rule.left) == 2
    assert rule.left[0]["cmdlet"] == "get-content"


def test_list_rules_returns_rule_objects(dbfile):
    rules = dbfile.list_rules()
    assert all(isinstance(r, Rule) for r in rules)
    assert [r.name for r in rules] == ["wave69-counts-equal-9002"]


def test_rules_accessor(dbfile):
    rules = dbfile.rules
    assert all(isinstance(r, Rule) for r in rules)
    assert [r.name for r in rules] == ["wave69-counts-equal-9002"]


def test_get_rule_missing(dbfile):
    with pytest.raises(KeyError):
        dbfile.get_rule("nope")


def test_add_rule_from_dict(dbfile):
    dbfile.add_rule({"name": "new-rule", "op": "eq"})
    assert dbfile.has_rule("new-rule")
    assert dbfile.get_rule("new-rule").op == "eq"


def test_add_rule_duplicate(dbfile):
    with pytest.raises(ValueError):
        dbfile.add_rule({"name": "wave69-counts-equal-9002"})


def test_update_rule(dbfile):
    rule = dbfile.update_rule("wave69-counts-equal-9002", op="lt")
    assert rule.op == "lt"
    assert dbfile.get_rule("wave69-counts-equal-9002").op == "lt"


def test_update_rule_unknown_field(dbfile):
    with pytest.raises(ValueError):
        dbfile.update_rule("wave69-counts-equal-9002", bogus_field=1)


def test_update_rule_cannot_rename_via_name_kwarg(dbfile):
    with pytest.raises(TypeError):
        dbfile.update_rule("wave69-counts-equal-9002", name="renamed-rule")


def test_rename_rule(dbfile):
    rule = dbfile.rename_rule("wave69-counts-equal-9002", "renamed-rule")
    assert rule.name == "renamed-rule"
    assert "wave69-counts-equal-9002" not in dbfile
    assert "renamed-rule" in dbfile


def test_rename_rule_to_existing_name(dbfile):
    dbfile.add_rule({"name": "other"})
    with pytest.raises(ValueError):
        dbfile.rename_rule("wave69-counts-equal-9002", "other")


def test_update_rule_missing(dbfile):
    with pytest.raises(KeyError):
        dbfile.update_rule("nope", op="eq")


def test_delete_rule(dbfile):
    deleted = dbfile.delete_rule("wave69-counts-equal-9002")
    assert deleted.name == "wave69-counts-equal-9002"
    assert len(dbfile) == 0


def test_delete_rule_missing(dbfile):
    with pytest.raises(KeyError):
        dbfile.delete_rule("nope")


def test_save_roundtrip(dbfile):
    dbfile.add_rule({"name": "second-rule", "op": "gt", "right": [
        {"cmdlet": "literal", "args": {"value": 5}},
    ]})
    dbfile.update_rule("wave69-counts-equal-9002", op="ne")
    dbfile.save()

    reloaded = DBFile(str(dbfile.resource_path))
    assert len(reloaded) == 2
    assert reloaded.get_rule("wave69-counts-equal-9002").op == "ne"
    assert reloaded.get_rule("second-rule").op == "gt"
    assert reloaded.get_rule("second-rule").right[0]["args"]["value"] == 5


def test_empty_file_creates_schema(tmp_path):
    db_file = tmp_path / "fresh.sqlite3"
    db_file.write_text("", encoding="utf-8")

    dbfile = DBFile(str(db_file))
    assert len(dbfile) == 0
    assert dbfile.list_rules() == []


def test_missing_file_raises(tmp_path):
    db_file = tmp_path / "nope.sqlite3"
    with pytest.raises(FileNotFoundError):
        DBFile(str(db_file))


def test_detects_sqlite_by_extension(tmp_path):
    db_file = tmp_path / "projects.sqlite"
    _insert_raw(db_file, SAMPLE)
    dbfile = DBFile(str(db_file))
    assert "wave69-counts-equal-9002" in dbfile

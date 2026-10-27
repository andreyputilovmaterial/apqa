"""Round-trip and CRUD tests for the YAML rules database."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from src.db_processors import DBFile
from src.db_processors.rule_base import Rule


SAMPLE = """\
- name: wave69-counts-equal-9002
  meta:
    tags: [counts, wave69]
    markers: []
  left:
    - cmdlet: get-content
      args:
        path: /path/to/specs.sav
    - cmdlet: count
  op: eq
  right:
    - cmdlet: literal
      args:
        value: 9002
"""


@pytest.fixture
def dbfile(tmp_path):
    db_file = tmp_path / "projects.yaml"
    db_file.write_text(SAMPLE, encoding="utf-8")
    return DBFile(str(db_file))


def test_load_rules(dbfile):
    assert len(dbfile) == 1
    assert "wave69-counts-equal-9002" in dbfile
    rule = dbfile.get_rule("wave69-counts-equal-9002")
    assert isinstance(rule, Rule)
    assert rule.op == "eq"
    assert rule.meta["tags"] == ["counts", "wave69"]
    assert len(rule.left) == 2
    assert rule.left[0]["cmdlet"] == "get-content"


def test_list_rules_returns_rule_objects(dbfile):
    rules = dbfile.list_rules()
    assert all(isinstance(r, Rule) for r in rules)
    assert [r.name for r in rules] == ["wave69-counts-equal-9002"]


def test_get_rule_missing(dbfile):
    with pytest.raises(KeyError):
        dbfile.get_rule("nope")


def test_add_rule_from_dict(dbfile):
    dbfile.add_rule({"name": "new-rule", "op": "eq"})
    assert dbfile.has_rule("new-rule")
    assert dbfile.get_rule("new-rule").op == "eq"


def test_add_rule_duplicate_id_raises(dbfile):
    with pytest.raises(ValueError):
        dbfile.add_rule({"name": "wave69-counts-equal-9002"})
    assert len(dbfile) == 1


def test_add_rule_explicit_duplicate_id_raises(dbfile):
    with pytest.raises(ValueError):
        dbfile.add_rule({"name": "different", "id": "wave69-counts-equal-9002"})
    assert len(dbfile) == 1


def test_update_rule(dbfile):
    rule = dbfile.update_rule("wave69-counts-equal-9002", op="lt")
    assert rule.op == "lt"
    assert dbfile.get_rule("wave69-counts-equal-9002").op == "lt"


def test_update_rule_unknown_field(dbfile):
    with pytest.raises(ValueError):
        dbfile.update_rule("wave69-counts-equal-9002", bogus_field=1)


def test_update_rule_cannot_change_id(dbfile):
    with pytest.raises(ValueError):
        dbfile.update_rule("wave69-counts-equal-9002", id="renamed-rule")


def test_rename_rule(dbfile):
    rule = dbfile.rename_rule("wave69-counts-equal-9002", "renamed-rule")
    assert rule.name == "renamed-rule"
    assert rule.id == "wave69-counts-equal-9002"
    assert "wave69-counts-equal-9002" in dbfile
    assert dbfile.get_rule("wave69-counts-equal-9002").name == "renamed-rule"


def test_rename_rule_allows_duplicate_display_name(dbfile):
    dbfile.add_rule({"name": "other"})
    rule = dbfile.rename_rule("wave69-counts-equal-9002", "other")
    assert rule.name == "other"
    assert rule.id == "wave69-counts-equal-9002"


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


def test_rule_from_dict_requires_name():
    with pytest.raises(ValueError):
        Rule.from_dict({"op": "eq"})


def test_rule_from_dict_non_mapping():
    with pytest.raises(ValueError):
        Rule.from_dict(["not", "a", "mapping"])


def test_rule_to_dict(dbfile):
    rule = dbfile.get_rule("wave69-counts-equal-9002")
    d = rule.to_dict()
    assert d["name"] == "wave69-counts-equal-9002"
    assert d["id"] == "wave69-counts-equal-9002"
    assert d["meta"]["tags"] == ["counts", "wave69"]


def test_op_args_roundtrip(dbfile):
    dbfile.add_rule({
        "name": "unordered-rule",
        "op": "eq",
        "op_args": {"unordered_arrays": True},
    })
    dbfile.save()

    reloaded = DBFile(str(dbfile.resource_path))
    assert reloaded.get_rule("unordered-rule").op_args == {"unordered_arrays": True}
def test_rule_from_dict_generates_id_from_display_name():
    rule = Rule.from_dict({"name": "properties for key art are matching"})
    assert rule.id == "properties-for-key-art-are-matching"
    assert rule.name == "properties for key art are matching"


def test_rule_from_dict_rejects_invalid_id():
    with pytest.raises(ValueError):
        Rule.from_dict({"name": "x", "id": "1 starts with a digit"})


def test_yaml_load_generates_ids_and_remaps_group_references(tmp_path):
    db_file = tmp_path / "projects.yaml"
    db_file.write_text(
        "\n".join([
            "groups:",
            "  - name: comp titles",
            "  - name: titles updated",
            "rules:",
            "  - name: list of comp titles matches excel",
            "    group: comp titles",
            "    op: eq",
        ]),
        encoding="utf-8",
    )
    dbfile = DBFile(str(db_file))

    group = dbfile.get_group("comp-titles")
    assert group.name == "comp titles"
    rule = dbfile.get_rule("list-of-comp-titles-matches-excel")
    assert rule.group == "comp-titles"




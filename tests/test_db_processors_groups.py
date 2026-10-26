"""CRUD tests for rule groups (folders) in YAML and SQLite."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from src.db_processors import DBFile
from src.db_processors.group_base import Group


# ---- YAML backend -----------------------------------------------------------

YAML_WITH_GROUPS = """\
groups:
  - name: Data
  - name: Metadata
    parent: Data
rules:
  - name: in-data
    group: Data
    op: eq
  - name: in-metadata
    group: Metadata
    op: ne
"""


@pytest.fixture
def yaml_dbfile(tmp_path):
    db_file = tmp_path / "projects.yaml"
    db_file.write_text(YAML_WITH_GROUPS, encoding="utf-8")
    return DBFile(str(db_file))


def test_yaml_loads_groups(yaml_dbfile):
    groups = yaml_dbfile.list_groups()
    assert [g.name for g in groups] == ["Data", "Metadata"]
    assert isinstance(groups[0], Group)
    assert yaml_dbfile.get_group("Metadata").parent == "Data"


def test_yaml_loads_rules_with_groups(yaml_dbfile):
    assert yaml_dbfile.get_rule("in-data").group == "Data"
    assert yaml_dbfile.get_rule("in-metadata").group == "Metadata"


def test_yaml_groups_accessor(yaml_dbfile):
    assert [g.name for g in yaml_dbfile.groups] == ["Data", "Metadata"]


def test_yaml_add_group(yaml_dbfile):
    yaml_dbfile.add_group({"name": "Routing"})
    assert yaml_dbfile.has_group("Routing")
    assert yaml_dbfile.get_group("Routing").parent == ""


def test_yaml_add_group_duplicate(yaml_dbfile):
    with pytest.raises(ValueError):
        yaml_dbfile.add_group({"name": "Data"})


def test_yaml_update_group_parent(yaml_dbfile):
    group = yaml_dbfile.update_group("Metadata", parent="")
    assert group.parent == ""
    assert yaml_dbfile.get_group("Metadata").parent == ""


def test_yaml_rename_group_cascades(yaml_dbfile):
    group = yaml_dbfile.rename_group("Data", "Core")
    assert group.name == "Core"
    assert not yaml_dbfile.has_group("Data")
    # child group's parent follows the rename
    assert yaml_dbfile.get_group("Metadata").parent == "Core"
    # rules in the renamed group follow too
    assert yaml_dbfile.get_rule("in-data").group == "Core"
    # rules in other groups are untouched
    assert yaml_dbfile.get_rule("in-metadata").group == "Metadata"


def test_yaml_delete_group(yaml_dbfile):
    yaml_dbfile.add_group({"name": "Empty"})
    deleted = yaml_dbfile.delete_group("Empty")
    assert deleted.name == "Empty"
    assert "Empty" not in {g.name for g in yaml_dbfile.list_groups()}


def test_yaml_delete_non_empty_group_refused(yaml_dbfile):
    with pytest.raises(ValueError):
        yaml_dbfile.delete_group("Data")


def test_yaml_save_roundtrip_groups(yaml_dbfile):
    yaml_dbfile.add_group({"name": "Routing", "parent": "Data"})
    yaml_dbfile.save()

    reloaded = DBFile(str(yaml_dbfile.resource_path))
    assert [g.name for g in reloaded.list_groups()] == ["Data", "Metadata", "Routing"]
    assert reloaded.get_group("Routing").parent == "Data"


# ---- parent validation (shared via base class) -------------------------------

def test_yaml_group_parent_must_exist(yaml_dbfile):
    with pytest.raises(ValueError):
        yaml_dbfile.add_group({"name": "Orphan", "parent": "Nope"})


def test_yaml_group_cannot_be_its_own_parent(yaml_dbfile):
    with pytest.raises(ValueError):
        yaml_dbfile.add_group({"name": "Loop", "parent": "Loop"})


def test_yaml_group_parent_cycle_refused(yaml_dbfile):
    yaml_dbfile.add_group({"name": "Child", "parent": "Data"})
    with pytest.raises(ValueError):
        yaml_dbfile.update_group("Data", parent="Child")


# ---- SQLite backend ---------------------------------------------------------

@pytest.fixture
def sqlite_dbfile(tmp_path):
    db_file = tmp_path / "projects.sqlite3"
    db_file.write_text("", encoding="utf-8")
    return DBFile(str(db_file))


def test_sqlite_add_and_list_groups(sqlite_dbfile):
    sqlite_dbfile.add_group({"name": "Data"})
    sqlite_dbfile.add_group({"name": "Metadata", "parent": "Data"})
    groups = sqlite_dbfile.list_groups()
    assert [g.name for g in groups] == ["Data", "Metadata"]
    assert sqlite_dbfile.get_group("Metadata").parent == "Data"


def test_sqlite_update_group_parent(sqlite_dbfile):
    sqlite_dbfile.add_group({"name": "Data"})
    sqlite_dbfile.add_group({"name": "Metadata"})
    group = sqlite_dbfile.update_group("Metadata", parent="Data")
    assert group.parent == "Data"


def test_sqlite_rename_group_cascades(sqlite_dbfile):
    sqlite_dbfile.add_group({"name": "Data"})
    sqlite_dbfile.add_group({"name": "Metadata", "parent": "Data"})
    sqlite_dbfile.add_rule({"name": "in-data", "group": "Data", "op": "eq"})

    group = sqlite_dbfile.rename_group("Data", "Core")
    assert group.name == "Core"
    assert not sqlite_dbfile.has_group("Data")
    assert sqlite_dbfile.get_group("Metadata").parent == "Core"
    assert sqlite_dbfile.get_rule("in-data").group == "Core"


def test_sqlite_delete_group(sqlite_dbfile):
    sqlite_dbfile.add_group({"name": "Empty"})
    deleted = sqlite_dbfile.delete_group("Empty")
    assert deleted.name == "Empty"
    assert not sqlite_dbfile.has_group("Empty")


def test_sqlite_delete_non_empty_group_refused(sqlite_dbfile):
    sqlite_dbfile.add_group({"name": "Data"})
    sqlite_dbfile.add_rule({"name": "r1", "group": "Data"})
    with pytest.raises(ValueError):
        sqlite_dbfile.delete_group("Data")


def test_sqlite_group_parent_must_exist(sqlite_dbfile):
    with pytest.raises(ValueError):
        sqlite_dbfile.add_group({"name": "Orphan", "parent": "Nope"})


def test_sqlite_group_roundtrip_reload(sqlite_dbfile):
    sqlite_dbfile.add_group({"name": "Data"})
    sqlite_dbfile.add_group({"name": "Metadata", "parent": "Data"})
    sqlite_dbfile.save()

    reloaded = DBFile(str(sqlite_dbfile.resource_path))
    assert [g.name for g in reloaded.list_groups()] == ["Data", "Metadata"]
    assert reloaded.get_group("Metadata").parent == "Data"


# ---- aliases on groups -------------------------------------------------------

YAML_WITH_GROUP_ALIASES = """\
groups:
  - name: Data
    aliases:
      - name: survey_mdd
        chain:
          - cmdlet: get-content-mdd
            args:
              path: s:/projects/p123/myfile.mdd
      - name: processed_data
        chain:
          - cmdlet: literal
            args:
              value: 42
rules:
  - name: r1
    group: Data
    op: eq
"""


def test_yaml_group_aliases_roundtrip(tmp_path):
    db_file = tmp_path / 'aliases.yaml'
    db_file.write_text(YAML_WITH_GROUP_ALIASES, encoding='utf-8')
    dbfile = DBFile(str(db_file))

    group = dbfile.get_group('Data')
    assert [a['name'] for a in group.aliases] == ['survey_mdd', 'processed_data']
    assert group.aliases[0]['chain'][0]['cmdlet'] == 'get-content-mdd'

    dbfile.save()
    reloaded = DBFile(str(db_file))
    assert [a['name'] for a in reloaded.get_group('Data').aliases] == [
        'survey_mdd', 'processed_data',
    ]


def test_yaml_group_update_aliases(yaml_dbfile):
    aliases = [{'name': 'x', 'chain': [{'cmdlet': 'literal', 'args': {'value': 1}}]}]
    group = yaml_dbfile.update_group('Data', aliases=aliases)
    assert [a['name'] for a in group.aliases] == ['x']


def test_yaml_group_aliases_duplicate_name_rejected(yaml_dbfile):
    with pytest.raises(ValueError):
        yaml_dbfile.add_group({
            'name': 'Dup',
            'aliases': [
                {'name': 'a', 'chain': []},
                {'name': 'a', 'chain': []},
            ],
        })


def test_yaml_group_alias_requires_name(yaml_dbfile):
    with pytest.raises(ValueError):
        yaml_dbfile.add_group({'name': 'Bad', 'aliases': [{'chain': []}]})


def test_sqlite_group_aliases_roundtrip(sqlite_dbfile):
    sqlite_dbfile.add_group({
        'name': 'Data',
        'aliases': [
            {'name': 'survey_mdd', 'chain': [{'cmdlet': 'get-content-mdd', 'args': {'path': 'x'}}]},
        ],
    })
    sqlite_dbfile.save()

    reloaded = DBFile(str(sqlite_dbfile.resource_path))
    aliases = reloaded.get_group('Data').aliases
    assert [a['name'] for a in aliases] == ['survey_mdd']
    assert aliases[0]['chain'][0]['cmdlet'] == 'get-content-mdd'


# ---- shared model behavior --------------------------------------------------

def test_group_from_dict_requires_name():
    with pytest.raises(ValueError):
        Group.from_dict({"parent": ""})


def test_group_from_dict_non_mapping():
    with pytest.raises(ValueError):
        Group.from_dict(["not", "a", "mapping"])


def test_group_to_dict_roundtrip():
    group = Group.from_dict({"name": "Data", "parent": "Root", "meta": {"comment": "x"}})
    d = group.to_dict()
    assert d["name"] == "Data"
    assert d["parent"] == "Root"
    assert d["meta"]["comment"] == "x"


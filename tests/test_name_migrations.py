"""Tests for upgrading cmdlet/op names stored in older database files."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.db_processors import DBFile
from src.db_processors.name_migrations import (
    migrate_chain,
    migrate_group_dict,
    migrate_op_name,
    migrate_rule_dict,
)


def test_migrate_op_name():
    assert migrate_op_name('eq') == 'cmp-eq'
    assert migrate_op_name('eq-unordered') == 'cmp-eq-unordered'
    assert migrate_op_name('cmp-eq') == 'cmp-eq'
    assert migrate_op_name('') == ''
    assert migrate_op_name(None) is None


def test_migrate_chain_rewrites_nested_cmdlet_names():
    chain = [
        {'cmdlet': 'get-content-excel', 'args': {'path': 'map.xlsx'}},
        {
            'cmdlet': 'bit-xor',
            'args': {
                'operands': [
                    [{'cmdlet': 'bit-lshift', 'args': {}}],
                    [{'cmdlet': 'get-content-text', 'args': {'path': 'f'}}],
                ],
            },
        },
    ]
    out = migrate_chain(chain)
    assert out[0]['cmdlet'] == 'get-content-excel'
    assert out[1]['cmdlet'] == 'bitwise-xor'
    assert out[1]['args']['operands'][0][0]['cmdlet'] == 'bitwise-lshift'
    assert out[1]['args']['operands'][1][0]['cmdlet'] == 'get-content-text'


def test_migrate_chain_leaves_plain_values_alone():
    chain = [{'cmdlet': 'literal', 'args': {'value': [1, 2, 3]}}]
    out = migrate_chain(chain)
    assert out[0]['args']['value'] == [1, 2, 3]


def test_migrate_rule_dict():
    data = {
        'name': 'r',
        'op': 'eq',
        'left': [{'cmdlet': 'and', 'args': {'operands': []}}],
        'right': [{'cmdlet': 'literal', 'args': {'value': 1}}],
    }
    out = migrate_rule_dict(data)
    assert out['op'] == 'cmp-eq'
    assert out['left'][0]['cmdlet'] == 'logical-and'
    assert out['right'][0]['cmdlet'] == 'literal'


def test_migrate_chain_rewrites_filter_to_exclude_deep_node():
    chain = [
        {
            'cmdlet': 'filter',
            'args': {'ignorelist': ['Fields.SnifferData.Fields.Cluster.Categories.Select']},
        },
    ]
    out = migrate_chain(chain)
    assert out[0]['cmdlet'] == 'exclude-deep-node'
    assert out[0]['args']['rules'] == [
        {
            'name': 'Fields.SnifferData.Fields.Cluster.Categories.Select',
            'type': 'eq',
            'pattern': 'Fields.SnifferData.Fields.Cluster.Categories.Select',
        },
    ]
    assert 'ignorelist' not in out[0]['args']


def test_migrate_chain_rewrites_matches_to_validate_text_matches():
    chain = [{'cmdlet': 'matches', 'args': {'pattern': 'world'}}]
    out = migrate_chain(chain)
    assert out[0]['cmdlet'] == 'validate-text-matches'
    assert out[0]['args'] == {'pattern': 'world'}


def test_migrate_chain_rewrites_map_to_foreach_item():
    chain = [
        {
            'cmdlet': 'map',
            'args': {'transform': [{'cmdlet': 'select-field', 'args': {'field': 'B'}}]},
        },
    ]
    out = migrate_chain(chain)
    assert out[0]['cmdlet'] == 'foreach-item'
    assert out[0]['args']['transform'][0]['cmdlet'] == 'select-field'


def test_migrate_chain_rewrites_length_to_transform_text_count_chars():
    chain = [{'cmdlet': 'length', 'args': {}}]
    out = migrate_chain(chain)
    assert out[0]['cmdlet'] == 'transform-text-count-chars'
    assert out[0]['args'] == {}


def test_migrate_group_dict_rewrites_alias_chains():
    data = {
        'name': 'g',
        'aliases': [{'name': 'a', 'chain': [{'cmdlet': 'not', 'args': {}}]}],
    }
    out = migrate_group_dict(data)
    assert out['aliases'][0]['chain'][0]['cmdlet'] == 'logical-not'


OLD_YAML = """\
rules:
  - name: legacy
    op: eq
    left:
      - cmdlet: bit-xor
        args:
          operands:
            - - cmdlet: bit-lshift
                args: {}
    right:
      - cmdlet: literal
        args:
          value: 1
"""


def test_yaml_load_migrates_old_names(tmp_path):
    db_file = tmp_path / 'projects.yaml'
    db_file.write_text(OLD_YAML, encoding='utf-8')

    dbfile = DBFile(str(db_file))
    rule = dbfile.get_rule('legacy')

    assert rule.op == 'cmp-eq'
    assert rule.left[0]['cmdlet'] == 'bitwise-xor'
    assert rule.left[0]['args']['operands'][0][0]['cmdlet'] == 'bitwise-lshift'
    assert rule.right[0]['cmdlet'] == 'literal'


def test_from_dict_migrates_op_and_chains():
    from src.db_processors.rule_base import Rule

    rule = Rule.from_dict({
        'name': 'r',
        'op': 'ne',
        'left': [{'cmdlet': 'or', 'args': {'operands': []}}],
        'right': [],
    })
    assert rule.op == 'cmp-ne'
    assert rule.left[0]['cmdlet'] == 'logical-or'

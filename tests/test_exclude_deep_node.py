"""Tests for the `exclude-deep-node` cmdlet (relative-path rule matching)."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from src.cmdlets.chain_runner import run_chain
from src.cmdlets.exclude_deep_node import exclude_deep_node
from src.cmdlets.value_types import Collection


def _literal(value):
    return {'cmdlet': 'literal', 'args': {'value': value}}


def _field(name):
    return {'cmdlet': 'select-field', 'args': {'field': name}}


def _rule(pattern, **kwargs):
    return {'pattern': pattern, **kwargs}


def _data():
    return {
        'Fields': {
            'SnifferData': {
                'Fields': {
                    'Cluster': {
                        'Categories': {
                            'Select': {'Label': '<-Select->'},
                            'Other': {'Label': 'Other'},
                        },
                    },
                },
            },
            'BrandAwareness': {'Label': 'ok'},
        },
    }


def test_removes_deep_leaf_at_root():
    result = run_chain([
        _literal(_data()),
        {'cmdlet': 'exclude-deep-node', 'args': {'rules': [
            _rule('Fields.SnifferData.Fields.Cluster.Categories.Select'),
        ]}},
    ])
    categories = result['Fields']['SnifferData']['Fields']['Cluster']['Categories']
    assert 'Select' not in categories
    assert categories['Other']['Label'] == 'Other'
    assert result['Fields']['BrandAwareness']['Label'] == 'ok'


def test_removes_whole_node():
    result = run_chain([
        _literal(_data()),
        {'cmdlet': 'exclude-deep-node', 'args': {'rules': [
            _rule('Fields.SnifferData.Fields.Cluster'),
        ]}},
    ])
    assert 'Cluster' not in result['Fields']['SnifferData']['Fields']


def test_matches_relative_to_received_value():
    # Placed mid-chain, rules are written against what the cmdlet receives
    # (SnifferData), not the root.
    result = run_chain([
        _literal(_data()),
        _field('Fields'),
        _field('SnifferData'),
        {'cmdlet': 'exclude-deep-node', 'args': {'rules': [
            _rule('Fields.Cluster'),
        ]}},
    ])
    assert result == {'Fields': {}}


def test_startswith():
    result = run_chain([
        _literal(_data()),
        {'cmdlet': 'exclude-deep-node', 'args': {'rules': [
            _rule('Fields.SnifferData', type='startswith'),
        ]}},
    ])
    assert 'SnifferData' not in result['Fields']
    assert 'BrandAwareness' in result['Fields']


def test_endswith():
    result = run_chain([
        _literal(_data()),
        {'cmdlet': 'exclude-deep-node', 'args': {'rules': [
            _rule('Select', type='endswith'),
        ]}},
    ])
    categories = result['Fields']['SnifferData']['Fields']['Cluster']['Categories']
    assert 'Select' not in categories
    assert 'Other' in categories


def test_contains():
    result = run_chain([
        _literal(_data()),
        {'cmdlet': 'exclude-deep-node', 'args': {'rules': [
            _rule('Categories.Select', type='contains'),
        ]}},
    ])
    categories = result['Fields']['SnifferData']['Fields']['Cluster']['Categories']
    assert 'Select' not in categories


def test_regex():
    result = run_chain([
        _literal(_data()),
        {'cmdlet': 'exclude-deep-node', 'args': {'rules': [
            _rule(r'Cluster\.Categories\.Select$', type='regex'),
        ]}},
    ])
    categories = result['Fields']['SnifferData']['Fields']['Cluster']['Categories']
    assert 'Select' not in categories
    assert 'Other' in categories


def test_case_insensitive():
    result = run_chain([
        _literal(_data()),
        {'cmdlet': 'exclude-deep-node', 'args': {'rules': [
            _rule('fields.snifferdata.fields.cluster.categories.select', case_insensitive=True),
        ]}},
    ])
    categories = result['Fields']['SnifferData']['Fields']['Cluster']['Categories']
    assert 'Select' not in categories


def test_case_sensitive_by_default():
    result = run_chain([
        _literal(_data()),
        {'cmdlet': 'exclude-deep-node', 'args': {'rules': [
            _rule('fields.snifferdata'),
        ]}},
    ])
    assert 'SnifferData' in result['Fields']


def test_removes_array_element():
    result = run_chain([
        _literal([{'name': 'a'}, {'name': 'b'}, {'name': 'c'}]),
        {'cmdlet': 'exclude-deep-node', 'args': {'rules': [_rule('[1]')]}},
    ])
    assert result == [{'name': 'a'}, {'name': 'c'}]


def test_removes_nested_array_element():
    result = exclude_deep_node(
        {'Pages': {'Q1': {'Elements': [{'Label': 'a'}, {'Label': 'b'}]}}},
        {'rules': [_rule('Pages.Q1.Elements[1]')]},
    )
    assert result == {'Pages': {'Q1': {'Elements': [{'Label': 'a'}]}}}


def test_ignores_path_outside_subtree():
    result = run_chain([
        _literal(_data()),
        _field('Fields'),
        _field('SnifferData'),
        {'cmdlet': 'exclude-deep-node', 'args': {'rules': [_rule('Other.x')]}},
    ])
    assert 'Cluster' in result['Fields']


def test_direct_call_and_scalar_passthrough():
    assert exclude_deep_node({'a': {'b': 1}}, {'rules': [_rule('a')]}) == {}
    assert exclude_deep_node(5, {'rules': [_rule('x')]}) == 5


def test_rejects_non_list_rules():
    with pytest.raises(TypeError, match='list of rule mappings'):
        exclude_deep_node({'a': 1}, {'rules': 'a.b'})


def test_rejects_rule_without_pattern():
    with pytest.raises(ValueError, match='non-empty "pattern"'):
        exclude_deep_node({'a': 1}, {'rules': [{'type': 'eq'}]})


def test_rejects_unknown_rule_type():
    with pytest.raises(ValueError, match='must be one of'):
        exclude_deep_node({'a': 1}, {'rules': [{'pattern': 'a', 'type': 'bogus'}]})


def test_matches_collection_element_by_name():
    data = {
        'Pages': {
            'Q1': {
                'Elements': Collection(
                    [{'Label': 'a'}, {'Label': 'b'}], ['first', 'second']
                ),
            },
        },
    }
    result = exclude_deep_node(
        data, {'rules': [_rule('Pages.Q1.Elements.second')]},
    )
    assert result == {'Pages': {'Q1': {'Elements': [{'Label': 'a'}]}}}


def test_matches_nested_field_below_named_element():
    data = {
        'Pages': {
            'Q1': {
                'Elements': Collection(
                    [{'Label': 'a'}, {'Label': 'b'}], ['first', 'second']
                ),
            },
        },
    }
    result = exclude_deep_node(
        data, {'rules': [_rule('Pages.Q1.Elements.second.Label')]},
    )
    assert result == {'Pages': {'Q1': {'Elements': [{'Label': 'a'}, {}]}}}

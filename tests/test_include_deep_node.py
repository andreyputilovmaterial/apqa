"""Tests for the `include-deep-node` cmdlet (relative-path rule matching)."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from src.cmdlets.chain_runner import run_chain
from src.cmdlets.include_deep_node import include_deep_node
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
                            'Select': {
                                'Label': '<-Select->',
                                '_Attrs': {'DataType': 1},
                                'Properties': {'x': 1},
                            },
                            'Other': {'Label': 'Other', '_Attrs': {'DataType': 2}},
                        },
                    },
                },
            },
            'BrandAwareness': {'Label': 'ok', '_Attrs': {'DataType': 3}},
        },
    }


def _labels_only():
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


def test_keeps_only_matching_leaves_and_scaffolding():
    result = run_chain([
        _literal(_data()),
        {'cmdlet': 'include-deep-node', 'args': {'rules': [
            _rule('.Label', type='endswith'),
        ]}},
    ])
    assert result == _labels_only()


def test_keeps_matched_subtree_wholesale():
    result = run_chain([
        _literal(_data()),
        {'cmdlet': 'include-deep-node', 'args': {'rules': [
            _rule('Fields.SnifferData.Fields.Cluster.Categories.Select'),
        ]}},
    ])
    assert result == {
        'Fields': {
            'SnifferData': {
                'Fields': {
                    'Cluster': {
                        'Categories': {
                            'Select': {
                                'Label': '<-Select->',
                                '_Attrs': {'DataType': 1},
                                'Properties': {'x': 1},
                            },
                        },
                    },
                },
            },
        },
    }


def test_matches_relative_to_received_value():
    result = run_chain([
        _literal(_data()),
        _field('Fields'),
        _field('SnifferData'),
        {'cmdlet': 'include-deep-node', 'args': {'rules': [
            _rule('.Label', type='endswith'),
        ]}},
    ])
    assert result == {
        'Fields': {
            'Cluster': {
                'Categories': {
                    'Select': {'Label': '<-Select->'},
                    'Other': {'Label': 'Other'},
                },
            },
        },
    }


def test_case_insensitive():
    result = run_chain([
        _literal(_data()),
        {'cmdlet': 'include-deep-node', 'args': {'rules': [
            _rule('.label', type='endswith', case_insensitive=True),
        ]}},
    ])
    assert result == _labels_only()


def test_keeps_array_elements_with_matching_field():
    result = run_chain([
        _literal([{'Label': 'a', 'X': 1}, {'Label': 'b', 'X': 2}]),
        {'cmdlet': 'include-deep-node', 'args': {'rules': [
            _rule('.Label', type='endswith'),
        ]}},
    ])
    assert result == [{'Label': 'a'}, {'Label': 'b'}]


def test_matches_nothing_returns_none():
    assert run_chain([
        _literal(_data()),
        {'cmdlet': 'include-deep-node', 'args': {'rules': [_rule('DoesNotExist')]}},
    ]) is None


def test_empty_rules_returns_none():
    assert include_deep_node({'a': 1}, {'rules': []}) is None


def test_scalar_root_without_match_returns_none():
    assert include_deep_node(5, {'rules': [_rule('x')]}) is None


def test_rejects_non_list_rules():
    with pytest.raises(TypeError, match='list of rule mappings'):
        include_deep_node({'a': 1}, {'rules': 'a.b'})


def test_rejects_rule_without_pattern():
    with pytest.raises(ValueError, match='non-empty "pattern"'):
        include_deep_node({'a': 1}, {'rules': [{'type': 'eq'}]})


def test_rejects_unknown_rule_type():
    with pytest.raises(ValueError, match='must be one of'):
        include_deep_node({'a': 1}, {'rules': [{'pattern': 'a', 'type': 'bogus'}]})


def test_keeps_collection_element_by_name():
    data = {
        'Pages': {
            'Q1': {
                'Elements': Collection(
                    [{'Label': 'a'}, {'Label': 'b'}], ['first', 'second']
                ),
            },
        },
    }
    result = include_deep_node(
        data, {'rules': [_rule('Pages.Q1.Elements.second')]},
    )
    assert result == {'Pages': {'Q1': {'Elements': [{'Label': 'b'}]}}}

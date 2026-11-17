"""Tests for the `filter` cmdlet (full-path string matching)."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from src.cmdlets.chain_runner import run_chain
from src.cmdlets.filter_ import filter_


def _field(name):
    return {'cmdlet': 'select-field', 'args': {'field': name}}


def _literal(value):
    return {'cmdlet': 'literal', 'args': {'value': value}}


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


def test_filter_removes_deep_leaf_at_root():
    result = run_chain([
        _literal(_data()),
        {'cmdlet': 'filter', 'args': {
            'ignorelist': ['Fields.SnifferData.Fields.Cluster.Categories.Select'],
        }},
    ])
    categories = result['Fields']['SnifferData']['Fields']['Cluster']['Categories']
    assert 'Select' not in categories
    assert categories['Other']['Label'] == 'Other'
    assert result['Fields']['BrandAwareness']['Label'] == 'ok'


def test_filter_removes_whole_node():
    result = run_chain([
        _literal(_data()),
        {'cmdlet': 'filter', 'args': {'ignorelist': ['Fields.SnifferData.Fields.Cluster']}},
    ])
    assert 'Cluster' not in result['Fields']['SnifferData']['Fields']


def test_filter_uses_full_path_mid_chain():
    result = run_chain([
        _literal(_data()),
        _field('Fields'),
        _field('SnifferData'),
        {'cmdlet': 'filter', 'args': {'ignorelist': ['Fields.SnifferData.Fields.Cluster']}},
    ])
    assert result == {'Fields': {}}


def test_filter_removes_array_element():
    result = run_chain([
        _literal([{'name': 'a'}, {'name': 'b'}, {'name': 'c'}]),
        {'cmdlet': 'filter', 'args': {'ignorelist': ['[1]']}},
    ])
    assert result == [{'name': 'a'}, {'name': 'c'}]


def test_filter_removes_nested_array_element():
    result = filter_(
        {'Pages': {'Q1': {'value': [{'Label': 'a'}, {'Label': 'b'}]}}},
        {'ignorelist': ['Pages.Q1.value[1]']},
    )
    assert result == {'Pages': {'Q1': {'value': [{'Label': 'a'}]}}}


def test_filter_ignores_path_outside_subtree():
    result = run_chain([
        _literal(_data()),
        _field('Fields'),
        _field('SnifferData'),
        {'cmdlet': 'filter', 'args': {'ignorelist': ['Fields.Other.x']}},
    ])
    assert 'Cluster' in result['Fields']


def test_filter_removes_whole_value_when_path_matches_position():
    result = run_chain([
        _literal(_data()),
        _field('Fields'),
        {'cmdlet': 'filter', 'args': {'ignorelist': ['Fields']}},
    ])
    assert result is None


def test_filter_direct_call():
    assert filter_({'a': {'b': 1}}, {'ignorelist': ['a']}) == {}
    assert filter_(5, {'ignorelist': ['x']}) == 5


def test_filter_rejects_non_string_path():
    with pytest.raises(ValueError, match='non-empty string'):
        filter_({'a': 1}, {'ignorelist': [42]})


def test_filter_rejects_ignorelist_not_a_list():
    with pytest.raises(TypeError, match='list of path strings'):
        filter_({'a': 1}, {'ignorelist': 'a.b'})

"""Tests for the `exclude-child` cmdlet (shallow direct-child rule matching)."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from src.cmdlets.exclude_child import exclude_child
from src.cmdlets.value_types import Collection


def _rule(pattern, **kwargs):
    return {'pattern': pattern, **kwargs}


def test_removes_matching_direct_child():
    assert exclude_child({'a': 1, 'b': 2}, {'rules': [_rule('a')]}) == {'b': 2}


def test_removes_multiple_by_startswith():
    value = {'SnifferData': 1, 'Sniffer': 2, 'BrandAwareness': 3}
    assert exclude_child(
        value, {'rules': [_rule('Sniffer', type='startswith')]},
    ) == {'BrandAwareness': 3}


def test_does_not_recurse():
    value = {'Fields': {'Cluster': {'Select': 1}}}
    assert exclude_child(value, {'rules': [_rule('Cluster')]}) == value


def test_removes_array_element():
    value = [{'name': 'a'}, {'name': 'b'}, {'name': 'c'}]
    assert exclude_child(value, {'rules': [_rule('[1]')]}) == [
        {'name': 'a'},
        {'name': 'c'},
    ]


def test_case_insensitive_key():
    assert exclude_child(
        {'SnifferData': 1, 'x': 2},
        {'rules': [_rule('snifferdata', case_insensitive=True)]},
    ) == {'x': 2}


def test_scalar_passthrough():
    assert exclude_child(5, {'rules': [_rule('x')]}) == 5


def test_empty_rules_means_noop():
    assert exclude_child({'a': 1}, {'rules': []}) == {'a': 1}
    assert exclude_child({'a': 1}, {}) == {'a': 1}


def test_rejects_non_list_rules():
    with pytest.raises(TypeError, match='list of rule mappings'):
        exclude_child({'a': 1}, {'rules': 'a'})


def test_rejects_rule_without_pattern():
    with pytest.raises(ValueError, match='non-empty "pattern"'):
        exclude_child({'a': 1}, {'rules': [{'type': 'eq'}]})


def test_removes_collection_element_by_name():
    value = Collection([{'name': 'a'}, {'name': 'b'}], ['first', 'second'])
    result = exclude_child(value, {'rules': [_rule('second')]})
    assert result == [{'name': 'a'}]
    assert result.names == ['first']

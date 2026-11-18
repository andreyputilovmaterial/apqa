"""Tests for the `include-child` cmdlet (shallow direct-child rule matching)."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from src.cmdlets.include_child import include_child
from src.cmdlets.value_types import Collection


def _rule(pattern, **kwargs):
    return {'pattern': pattern, **kwargs}


def test_keeps_matching_direct_child():
    assert include_child({'a': 1, 'b': 2}, {'rules': [_rule('a')]}) == {'a': 1}


def test_keeps_multiple_by_startswith():
    value = {'SnifferData': 1, 'Sniffer': 2, 'BrandAwareness': 3}
    assert include_child(
        value, {'rules': [_rule('Sniffer', type='startswith')]},
    ) == {'SnifferData': 1, 'Sniffer': 2}


def test_does_not_recurse():
    value = {'Fields': {'Cluster': {'Select': 1}}}
    # Only 'Fields' is a direct child; 'Cluster' is not, so nothing is kept.
    assert include_child(value, {'rules': [_rule('Cluster')]}) is None


def test_keeps_array_element():
    value = [{'name': 'a'}, {'name': 'b'}, {'name': 'c'}]
    assert include_child(value, {'rules': [_rule('[1]')]}) == [{'name': 'b'}]


def test_case_insensitive_key():
    assert include_child(
        {'SnifferData': 1, 'x': 2},
        {'rules': [_rule('snifferdata', case_insensitive=True)]},
    ) == {'SnifferData': 1}


def test_scalar_root_returns_none():
    assert include_child(5, {'rules': [_rule('x')]}) is None


def test_empty_rules_returns_none():
    assert include_child({'a': 1}, {'rules': []}) is None
    assert include_child({'a': 1}, {}) is None


def test_rejects_non_list_rules():
    with pytest.raises(TypeError, match='list of rule mappings'):
        include_child({'a': 1}, {'rules': 'a'})


def test_rejects_rule_without_pattern():
    with pytest.raises(ValueError, match='non-empty "pattern"'):
        include_child({'a': 1}, {'rules': [{'type': 'eq'}]})


def test_keeps_collection_element_by_name():
    value = Collection([{'name': 'a'}, {'name': 'b'}], ['first', 'second'])
    result = include_child(value, {'rules': [_rule('second')]})
    assert result == [{'name': 'b'}]
    assert result.names == ['second']

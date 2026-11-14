"""Tests for the shape-changing cmdlets: select-field, select-item, select-range,
map, and where."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from src.cmdlets import cmdlets
from src.cmdlets.sysmissing import sysmissing
from src.rule_runner import run_rule


def _literal(value):
    return {'cmdlet': 'literal', 'args': {'value': value}}


def _field(name):
    return {'cmdlet': 'select-field', 'args': {'field': name}}


# ---- select-field ----------------------------------------------------------

def test_select_field_reads_block_field_scalar():
    assert cmdlets.get('select-field')({'a': 1, 'b': 2}, {'field': 'a'}) == 1


def test_select_field_reads_block_field_compound():
    value = {'a': [1, 2], 'b': {'x': 1}}
    assert cmdlets.get('select-field')(value, {'field': 'a'}) == [1, 2]
    assert cmdlets.get('select-field')(value, {'field': 'b'}) == {'x': 1}


def test_select_field_flattens_array():
    rows = [{'B': 'x'}, {'B': 'y'}]
    assert cmdlets.get('select-field')(rows, {'field': 'B'}) == ['x', 'y']


def test_select_field_empty_array():
    assert cmdlets.get('select-field')([], {'field': 'B'}) == []


def test_select_field_missing_field_in_block_raises():
    with pytest.raises(ValueError):
        cmdlets.get('select-field')({'a': 1}, {'field': 'b'})


def test_select_field_missing_field_in_element_raises():
    with pytest.raises(ValueError):
        cmdlets.get('select-field')([{'a': 1}, {}], {'field': 'b'})


def test_select_field_requires_field_arg():
    with pytest.raises(ValueError):
        cmdlets.get('select-field')({'a': 1}, {})


def test_select_field_accepts_empty_field_name():
    # An empty string is a valid field name (Python `d[''] = 3` works); only a
    # missing (None) field name is rejected.
    assert cmdlets.get('select-field')({'': 3}, {'field': ''}) == 3


def test_select_field_rejects_scalar_and_sysmissing():
    with pytest.raises(TypeError):
        cmdlets.get('select-field')(5, {'field': 'a'})
    with pytest.raises(TypeError):
        cmdlets.get('select-field')(sysmissing, {'field': 'a'})


def test_select_field_rejects_non_block_element():
    with pytest.raises(TypeError):
        cmdlets.get('select-field')([1], {'field': 'a'})


# ---- select-item -----------------------------------------------------------

def test_select_item_by_index():
    assert cmdlets.get('select-item')(['a', 'b', 'c'], {'index': 1}) == 'b'


def test_select_item_negative_index():
    assert cmdlets.get('select-item')(['a', 'b', 'c'], {'index': -1}) == 'c'


def test_select_item_out_of_range_raises():
    with pytest.raises(ValueError):
        cmdlets.get('select-item')(['a'], {'index': 5})


def test_select_item_requires_index():
    with pytest.raises(ValueError):
        cmdlets.get('select-item')(['a'], {})


def test_select_item_index_must_be_integer():
    with pytest.raises(TypeError):
        cmdlets.get('select-item')(['a'], {'index': 1.5})
    with pytest.raises(TypeError):
        cmdlets.get('select-item')(['a'], {'index': True})


def test_select_item_rejects_non_array():
    with pytest.raises(TypeError):
        cmdlets.get('select-item')({'a': 1}, {'index': 0})


# ---- select-range ----------------------------------------------------------

def test_select_range_start_stop():
    assert cmdlets.get('select-range')([0, 1, 2, 3, 4], {'start': 1, 'stop': 3}) == [1, 2]


def test_select_range_stop_only():
    assert cmdlets.get('select-range')([0, 1, 2], {'stop': 1}) == [0]


def test_select_range_start_only():
    assert cmdlets.get('select-range')([0, 1, 2], {'start': 1}) == [1, 2]


def test_select_range_no_bounds_is_full_copy():
    assert cmdlets.get('select-range')([0, 1], {}) == [0, 1]


def test_select_range_start_past_stop_is_empty():
    assert cmdlets.get('select-range')([0, 1, 2], {'start': 2, 'stop': 1}) == []


def test_select_range_rejects_non_array():
    with pytest.raises(TypeError):
        cmdlets.get('select-range')({'a': 1}, {})


def test_select_range_bounds_must_be_integer():
    with pytest.raises(TypeError):
        cmdlets.get('select-range')([0, 1], {'start': 1.5})


# ---- map -------------------------------------------------------------------

def test_map_transforms_each_iteration():
    rows = [{'B': 1}, {'B': 2}]
    transform = [_field('B')]
    assert cmdlets.get('map')(rows, {'transform': transform}) == [1, 2]


def test_map_transform_can_change_type():
    assert cmdlets.get('map')(['1', '2'], {'transform': [{'cmdlet': 'as-integer'}]}) == [1, 2]


def test_map_empty_array():
    assert cmdlets.get('map')([], {'transform': [_field('B')]}) == []


def test_map_requires_non_empty_transform():
    with pytest.raises(ValueError):
        cmdlets.get('map')([1], {})
    with pytest.raises(ValueError):
        cmdlets.get('map')([1], {'transform': []})


def test_map_rejects_non_array():
    with pytest.raises(TypeError):
        cmdlets.get('map')({'a': 1}, {'transform': [_field('a')]})


# ---- where -----------------------------------------------------------------

def test_where_keeps_truthy_iterations():
    rows = [{'x': 0}, {'x': 1}]
    predicate = [_field('x')]
    assert cmdlets.get('where')(rows, {'predicate': predicate}) == [{'x': 1}]


def test_where_empty_array():
    assert cmdlets.get('where')([], {'predicate': [_field('x')]}) == []


def test_where_requires_non_empty_predicate():
    with pytest.raises(ValueError):
        cmdlets.get('where')([1], {})
    with pytest.raises(ValueError):
        cmdlets.get('where')([1], {'predicate': []})


def test_where_rejects_non_array():
    with pytest.raises(TypeError):
        cmdlets.get('where')({'a': 1}, {'predicate': [_field('a')]})


# ---- rule runner end-to-end ------------------------------------------------

def test_help_example_pipeline():
    rule = {
        'left': [
            _literal({'Title Details': [{'B': 'x'}, {'B': 'y'}]}),
            _field('Title Details'),
            _field('B'),
            {'cmdlet': 'count'},
        ],
        'op': 'eq',
        'right': [_literal(2)],
    }
    assert run_rule(rule) is True


def test_map_pipeline():
    rule = {
        'left': [
            _literal([{'B': 1}, {'B': 2}]),
            {'cmdlet': 'map', 'args': {'transform': [_field('B')]}},
        ],
        'op': 'eq',
        'right': [_literal([1, 2])],
    }
    assert run_rule(rule) is True


def test_where_pipeline():
    rule = {
        'left': [
            _literal([{'x': 0}, {'x': 1}]),
            {'cmdlet': 'where', 'args': {'predicate': [_field('x')]}},
        ],
        'op': 'eq',
        'right': [_literal([{'x': 1}])],
    }
    assert run_rule(rule) is True

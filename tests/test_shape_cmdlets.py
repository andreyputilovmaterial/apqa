"""Tests for the shape-changing cmdlets: select-field, select-item, select-range,
foreach-item, and sort."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from src.cmdlets import cmdlets
from src.cmdlets.sysmissing import sysmissing
from src.cmdlets.value_types import Collection
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


def test_select_field_missing_ok_returns_sysmissing_for_block():
    assert cmdlets.get('select-field')(
        {'a': 1}, {'field': 'b', 'missing_ok': True}
    ) is sysmissing


def test_select_field_missing_ok_returns_sysmissing_per_element():
    rows = Collection([{'a': 1}, {}], ['r1', 'r2'])
    result = cmdlets.get('select-field')(rows, {'field': 'a', 'missing_ok': True})
    assert result[0] == 1
    assert result[1] is sysmissing
    assert result.names == ['r1', 'r2']


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


def test_select_field_missing_ok_still_rejects_scalar_and_sysmissing():
    with pytest.raises(TypeError):
        cmdlets.get('select-field')(5, {'field': 'a', 'missing_ok': True})
    with pytest.raises(TypeError):
        cmdlets.get('select-field')(sysmissing, {'field': 'a', 'missing_ok': True})


def test_select_field_rejects_non_block_element():
    with pytest.raises(TypeError):
        cmdlets.get('select-field')([1], {'field': 'a'})


def test_select_field_missing_ok_still_rejects_non_block_element():
    with pytest.raises(TypeError):
        cmdlets.get('select-field')([1], {'field': 'a', 'missing_ok': True})


# ---- select-item -----------------------------------------------------------

def test_select_item_by_index():
    assert cmdlets.get('select-item')(['a', 'b', 'c'], {'index': 1}) == 'b'


def test_select_item_negative_index():
    assert cmdlets.get('select-item')(['a', 'b', 'c'], {'index': -1}) == 'c'


def test_select_item_out_of_range_raises():
    with pytest.raises(ValueError):
        cmdlets.get('select-item')(['a'], {'index': 5})


def test_select_item_missing_ok_returns_sysmissing():
    assert cmdlets.get('select-item')(
        ['a'], {'index': 5, 'missing_ok': True}
    ) is sysmissing


def test_select_item_missing_ok_negative_out_of_range():
    assert cmdlets.get('select-item')(
        ['a'], {'index': -5, 'missing_ok': True}
    ) is sysmissing


def test_select_item_requires_index():
    with pytest.raises(ValueError):
        cmdlets.get('select-item')(['a'], {})


def test_select_item_index_must_be_integer():
    with pytest.raises(TypeError):
        cmdlets.get('select-item')(['a'], {'index': 1.5})
    with pytest.raises(TypeError):
        cmdlets.get('select-item')(['a'], {'index': True})


def test_select_item_missing_ok_still_requires_integer_index():
    with pytest.raises(TypeError):
        cmdlets.get('select-item')(['a'], {'index': 1.5, 'missing_ok': True})
    with pytest.raises(TypeError):
        cmdlets.get('select-item')(['a'], {'index': True, 'missing_ok': True})


def test_select_item_rejects_non_array():
    with pytest.raises(TypeError):
        cmdlets.get('select-item')({'a': 1}, {'index': 0})


def test_select_item_missing_ok_still_rejects_non_array():
    with pytest.raises(TypeError):
        cmdlets.get('select-item')({'a': 1}, {'index': 0, 'missing_ok': True})


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


# ---- rule runner end-to-end ------------------------------------------------

def test_help_example_pipeline():
    rule = {
        'left': [
            _literal({'Title Details': [{'B': 'x'}, {'B': 'y'}]}),
            _field('Title Details'),
            _field('B'),
            {'cmdlet': 'count'},
        ],
        'op': 'cmp-eq',
        'right': [_literal(2)],
    }
    assert run_rule(rule) is True


# ---- collections (no plain lists) -------------------------------------------

def test_literal_list_becomes_collection():
    result = cmdlets.get('literal')(None, {'value': [1, 2]})
    assert isinstance(result, Collection)
    assert result.names == ['1', '2']


def test_select_field_preserves_collection_names():
    rows = Collection([{'B': 'x'}, {'B': 'y'}], ['r1', 'r2'])
    result = cmdlets.get('select-field')(rows, {'field': 'B'})
    assert isinstance(result, Collection)
    assert result.names == ['r1', 'r2']


def test_select_range_preserves_collection_names():
    coll = Collection([0, 1, 2, 3], ['a', 'b', 'c', 'd'])
    result = cmdlets.get('select-range')(coll, {'start': 1, 'stop': 3})
    assert isinstance(result, Collection)
    assert result.names == ['b', 'c']


def test_foreach_item_preserves_collection_names():
    rows = Collection([{'x': 1}, {'x': 2}], ['a', 'b'])
    result = cmdlets.get('foreach-item')(rows, {'transform': [_field('x')]})
    assert isinstance(result, Collection)
    assert result.names == ['a', 'b']


def test_sort_preserves_collection_names():
    rows = Collection([{'x': 2}, {'x': 1}], ['two', 'one'])
    result = cmdlets.get('sort')(rows, {'by': 'x'})
    assert isinstance(result, Collection)
    assert result.names == ['one', 'two']

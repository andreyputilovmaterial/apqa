"""Tests for the foreach-* cmdlets: foreach-item, foreach-field, foreach-deep-node."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from src.cmdlets import cmdlets
from src.cmdlets.meta import get_cmdlet_metadata
from src.cmdlets.sysmissing import sysmissing
from src.rule_runner import run_rule


def _literal(value):
    return {'cmdlet': 'literal', 'args': {'value': value}}


def _field(name):
    return {'cmdlet': 'select-field', 'args': {'field': name}}


def _as_integer():
    return {'cmdlet': 'as-integer'}


def _as_text():
    return {'cmdlet': 'as-text'}


# ---- foreach-item -----------------------------------------------------------

def test_foreach_item_transforms_each_item():
    rows = [{'B': 1}, {'B': 2}]
    transform = [_field('B')]
    assert cmdlets.get('foreach-item')(rows, {'transform': transform}) == [1, 2]


def test_foreach_item_can_change_type():
    assert cmdlets.get('foreach-item')(['1', '2'], {'transform': [_as_integer()]}) == [1, 2]


def test_foreach_item_empty_array():
    assert cmdlets.get('foreach-item')([], {'transform': [_field('B')]}) == []


def test_foreach_item_requires_non_empty_transform():
    with pytest.raises(ValueError):
        cmdlets.get('foreach-item')([1], {})
    with pytest.raises(ValueError):
        cmdlets.get('foreach-item')([1], {'transform': []})


def test_foreach_item_rejects_non_array():
    with pytest.raises(TypeError):
        cmdlets.get('foreach-item')({'a': 1}, {'transform': [_field('a')]})


# ---- foreach-field ----------------------------------------------------------

def test_foreach_field_transforms_each_field():
    block = {'a': '1', 'b': '2'}
    assert cmdlets.get('foreach-field')(block, {'transform': [_as_integer()]}) == {
        'a': 1,
        'b': 2,
    }


def test_foreach_field_pipes_each_field_value():
    # The field value (a block here), not the whole outer block, is the piped input.
    block = {'a': {'x': 1}, 'b': {'x': 2}}
    transform = [_field('x')]
    assert cmdlets.get('foreach-field')(block, {'transform': transform}) == {
        'a': 1,
        'b': 2,
    }


def test_foreach_field_empty_block():
    assert cmdlets.get('foreach-field')({}, {'transform': [_as_text()]}) == {}


def test_foreach_field_requires_non_empty_transform():
    with pytest.raises(ValueError):
        cmdlets.get('foreach-field')({'a': 1}, {})
    with pytest.raises(ValueError):
        cmdlets.get('foreach-field')({'a': 1}, {'transform': []})


def test_foreach_field_rejects_non_block():
    with pytest.raises(TypeError):
        cmdlets.get('foreach-field')([1, 2], {'transform': [_as_text()]})
    with pytest.raises(TypeError):
        cmdlets.get('foreach-field')(5, {'transform': [_as_text()]})
    with pytest.raises(TypeError):
        cmdlets.get('foreach-field')(sysmissing, {'transform': [_as_text()]})


# ---- foreach-deep-node ------------------------------------------------------

def test_foreach_deep_node_transforms_every_leaf():
    value = {'a': {'b': '1', 'c': ['2', '3']}, 'd': '4'}
    assert cmdlets.get('foreach-deep-node')(value, {'transform': [_as_integer()]}) == {
        'a': {'b': 1, 'c': [2, 3]},
        'd': 4,
    }


def test_foreach_deep_node_transforms_sysmissing_leaves():
    assert cmdlets.get('foreach-deep-node')({'a': None}, {'transform': [_as_text()]}) == {
        'a': '',
    }


def test_foreach_deep_node_scalar_root():
    assert cmdlets.get('foreach-deep-node')('1', {'transform': [_as_integer()]}) == 1


def test_foreach_deep_node_empty_compounds_keep_shape():
    assert cmdlets.get('foreach-deep-node')({}, {'transform': [_as_text()]}) == {}
    assert cmdlets.get('foreach-deep-node')([], {'transform': [_as_text()]}) == []


def test_foreach_deep_node_requires_non_empty_transform():
    with pytest.raises(ValueError):
        cmdlets.get('foreach-deep-node')({'a': 1}, {})
    with pytest.raises(ValueError):
        cmdlets.get('foreach-deep-node')({'a': 1}, {'transform': []})


# ---- rule runner end-to-end -------------------------------------------------

def test_foreach_item_pipeline():
    rule = {
        'left': [
            _literal([{'B': 1}, {'B': 2}]),
            {'cmdlet': 'foreach-item', 'args': {'transform': [_field('B')]}},
        ],
        'op': 'cmp-eq',
        'right': [_literal([1, 2])],
    }
    assert run_rule(rule) is True


def test_foreach_field_pipeline():
    rule = {
        'left': [
            _literal({'a': '1', 'b': '2'}),
            {'cmdlet': 'foreach-field', 'args': {'transform': [_as_integer()]}},
        ],
        'op': 'cmp-eq',
        'right': [_literal({'a': 1, 'b': 2})],
    }
    assert run_rule(rule) is True


def test_foreach_deep_node_pipeline():
    rule = {
        'left': [
            _literal({'a': {'b': '1'}}),
            {'cmdlet': 'foreach-deep-node', 'args': {'transform': [_as_integer()]}},
        ],
        'op': 'cmp-eq',
        'right': [_literal({'a': {'b': 1}})],
    }
    assert run_rule(rule) is True


# ---- editor metadata --------------------------------------------------------

def test_foreach_cmdlet_metadata():
    meta = {c['name']: c for c in get_cmdlet_metadata()['cmdlets']}
    for name in ('foreach-item', 'foreach-field', 'foreach-deep-node'):
        assert meta[name]['kind'] == 'processor'
        assert meta[name]['permissions'] == ['deps-stdlib-only']
        transform = {a['name']: a for a in meta[name]['args']}['transform']
        assert transform['type'] == 'cmdlet-chain'
        assert transform['required'] is True

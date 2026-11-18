"""Tests for the cmdlet value-type taxonomy (src/cmdlets/value_types.py)."""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.cmdlets import value_types as vt


def test_scalar_categories_map_to_plain_python():
    assert vt.Text is str
    assert vt.Integer is int
    assert vt.Real is float
    assert vt.Boolean is bool
    assert vt.PathValue is Path


def test_value_taxonomy_exports_expected_names():
    for name in (
        'Value', 'PipeValue', 'Scalar', 'Compound',
        'Text', 'Integer', 'Real', 'Boolean', 'PathValue', 'DateTime',
        'CategoricalSingle', 'CategoricalMulti',
        'Block', 'Collection',
    ):
        assert hasattr(vt, name)


def test_compound_types_are_classes():
    for name in ('Value', 'Scalar', 'Compound', 'Block', 'Collection'):
        assert isinstance(getattr(vt, name), type)


def test_collection_is_a_list_with_dual_access():
    coll = vt.Collection([{'Name': 'A'}, {'Name': 'B'}], ['A', 'B'])
    assert isinstance(coll, list)
    assert coll[0] == {'Name': 'A'}
    assert coll[1] == {'Name': 'B'}
    assert coll.names == ['A', 'B']
    assert coll.by_name == {'A': 0, 'B': 1}
    assert coll.index_of('B') == 1
    assert coll.get('A') == {'Name': 'A'}
    assert coll.get('missing') is None


def test_collection_default_names_are_one_based():
    coll = vt.Collection([10, 20, 30])
    assert coll.names == ['1', '2', '3']
    assert coll.index_of('3') == 2


def test_collection_rejects_duplicate_names():
    with pytest.raises(ValueError, match='duplicate element name'):
        vt.Collection([1, 2], ['x', 'x'])


def test_collection_rejects_name_length_mismatch():
    with pytest.raises(ValueError, match='items but'):
        vt.Collection([1, 2], ['x'])


def test_block_is_a_dict_with_dual_access():
    block = vt.Block({'a': 1, 'b': 2})
    assert isinstance(block, dict)
    assert block['a'] == 1
    assert block.child_at(1) == 2
    assert block.field_name_at(0) == 'a'
    assert list(block.children()) == [('a', 1), ('b', 2)]


def test_collection_children():
    coll = vt.Collection([10, 20], ['x', 'y'])
    assert list(coll.children()) == [(0, 10), (1, 20)]


def test_block_and_collection_subclass_compound():
    assert issubclass(vt.Block, vt.Compound)
    assert issubclass(vt.Collection, vt.Compound)
    assert issubclass(vt.Block, vt.Value)
    assert issubclass(vt.Collection, vt.Value)
    assert isinstance(vt.Block(), vt.Compound)
    assert isinstance(vt.Collection(), vt.Compound)


def test_from_plain_converts_lists_recursively():
    value = vt.from_plain({'a': [1, 2], 'b': {'c': [3]}})
    assert isinstance(value, vt.Block)
    assert isinstance(value['a'], vt.Collection)
    assert value['a'].names == ['1', '2']
    assert isinstance(value['b'], vt.Block)
    assert isinstance(value['b']['c'], vt.Collection)
    assert value['b']['c'].names == ['1']


def test_from_plain_preserves_existing_collection_names():
    coll = vt.Collection([{'x': 1}], ['kept'])
    value = vt.from_plain(coll)
    assert isinstance(value, vt.Collection)
    assert value.names == ['kept']


def test_from_plain_leaves_scalars_untouched():
    assert vt.from_plain(5) == 5
    assert vt.from_plain('x') == 'x'
    assert vt.from_plain(None) is None

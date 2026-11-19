"""Tests for the cmdlet value-type taxonomy (src/cmdlets/value_types)."""

import sys
from datetime import date
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.cmdlets import value_types as vt


def test_value_taxonomy_exports_expected_names():
    for name in (
        'Value', 'PipeValue', 'Scalar', 'Compound', 'SysMissing',
        'Text', 'Integer', 'Real', 'Boolean', 'PathValue', 'DateTime',
        'CategoricalSingle', 'CategoricalMulti',
        'Block', 'Collection',
        'from_plain', 'from_serialized', 'to_serialized', 'coerce',
        'format_path', 'sysmissing', 'is_sysmissing',
    ):
        assert hasattr(vt, name)


def test_hierarchy():
    assert issubclass(vt.Scalar, vt.Value)
    assert issubclass(vt.Compound, vt.Value)
    assert issubclass(vt.SysMissing, vt.Value)
    assert issubclass(vt.Block, vt.Compound)
    assert issubclass(vt.Collection, vt.Compound)
    assert issubclass(vt.Text, vt.Scalar)
    assert issubclass(vt.Integer, vt.Scalar)


def test_scalar_wrappers_expose_value_and_type_name():
    assert vt.Text('x').value == 'x'
    assert vt.Text('x').type_name == 'text'
    assert vt.Integer(42).value == 42
    assert vt.Real(3.14).value == 3.14
    assert vt.Boolean(True).value is True
    assert vt.PathValue(Path('/tmp/x')).value == Path('/tmp/x')
    assert vt.DateTime(date(2025, 7, 15)).value == date(2025, 7, 15)


def test_scalar_equality_with_raw_value():
    assert vt.Text('x') == 'x'
    assert vt.Integer(42) == 42
    assert vt.Real(3.14) == 3.14
    assert vt.Boolean(True) == True  # noqa: E712


def test_boolean_is_distinct_from_number():
    assert vt.Boolean(True) != vt.Integer(1)
    assert vt.Boolean(False) != vt.Integer(0)


def test_integer_and_real_compare_numerically():
    assert vt.Integer(1) == vt.Real(1.0)
    assert vt.Integer(1) < vt.Real(2.0)


def test_sysmissing_singleton():
    assert vt.is_sysmissing(vt.sysmissing)
    assert vt.sysmissing is not None
    assert not vt.sysmissing
    assert vt.sysmissing.value is None
    assert vt.sysmissing == vt.sysmissing
    assert vt.sysmissing == None  # noqa: E711


def test_collection_is_a_list_with_dual_access():
    coll = vt.Collection([{'Name': 'A'}, {'Name': 'B'}], ['A', 'B'])
    assert isinstance(coll, list)
    assert coll[0] == {'Name': 'A'}
    assert coll.names == ['A', 'B']
    assert coll.by_name == {'A': 0, 'B': 1}
    assert coll.index_of('B') == 1
    assert coll.get('A') == {'Name': 'A'}
    assert coll.get('missing') is None
    assert coll.item(1) == {'Name': 'B'}
    assert coll.item_by_name('A') == {'Name': 'A'}


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


def test_collection_auto_wraps_items():
    coll = vt.Collection([1, 'x', None])
    assert isinstance(coll[0], vt.Integer)
    assert isinstance(coll[1], vt.Text)
    assert coll[2] is vt.sysmissing


def test_block_is_a_dict_with_field_access():
    block = vt.Block({'a': 1, 'b': 2})
    assert isinstance(block, dict)
    assert block['a'] == 1
    assert block.field('b') == 2
    assert block.select_field('a') == 1
    assert block.child_at(1) == 2
    assert block.field_name_at(0) == 'a'
    assert list(block.children()) == [('a', vt.Integer(1)), ('b', vt.Integer(2))]


def test_block_auto_wraps_fields():
    block = vt.Block({'a': 'x', 'b': None})
    assert isinstance(block['a'], vt.Text)
    assert block['b'] is vt.sysmissing


def test_block_missing_field_raises_value_error():
    with pytest.raises(ValueError, match='not found'):
        vt.Block({'a': 1}).field('b')


def test_collection_children():
    coll = vt.Collection([10, 20], ['x', 'y'])
    assert list(coll.children()) == [
        (0, 'x', vt.Integer(10)),
        (1, 'y', vt.Integer(20)),
    ]


def test_from_plain_wraps_scalars_and_compounds():
    value = vt.from_plain({'a': [1, 2], 'b': {'c': 'x'}, 'd': None, 'e': True})
    assert isinstance(value, vt.Block)
    assert isinstance(value['a'], vt.Collection)
    assert value['a'].names == ['1', '2']
    assert isinstance(value['a'][0], vt.Integer)
    assert isinstance(value['b'], vt.Block)
    assert isinstance(value['b']['c'], vt.Text)
    assert value['d'] is vt.sysmissing
    assert isinstance(value['e'], vt.Boolean)


def test_from_plain_is_idempotent_on_values():
    coll = vt.Collection([{'x': 1}], ['kept'])
    value = vt.from_plain(coll)
    assert value is coll


def test_from_plain_wraps_scalars():
    assert vt.from_plain(5) == 5
    assert isinstance(vt.from_plain(5), vt.Integer)
    assert isinstance(vt.from_plain('x'), vt.Text)
    assert vt.from_plain(None) is vt.sysmissing


def test_serialized_round_trip():
    original = vt.from_plain({'a': [1, 'x', None]})
    data = vt.to_serialized(original)
    restored = vt.from_serialized(data)
    assert restored == original


def test_serialized_path_and_sysmissing():
    assert vt.to_serialized(vt.PathValue(Path('/tmp/x'))) == {
        'type': 'path', 'value': '/tmp/x',
    }
    assert vt.to_serialized(vt.sysmissing) == {'type': 'sysmissing'}
    assert vt.from_serialized({'type': 'sysmissing'}) is vt.sysmissing
    assert vt.from_serialized({'type': 'path', 'value': '/tmp/x'}) == vt.PathValue(Path('/tmp/x'))


def test_from_serialized_accepts_bare_json():
    assert vt.from_serialized(42) == 42
    assert vt.from_serialized(None) is vt.sysmissing


def test_coerce():
    assert vt.coerce(5) == 5
    assert isinstance(vt.coerce(5), vt.Integer)
    assert vt.coerce(None) is vt.sysmissing
    assert vt.coerce(vt.Text('x')) == 'x'



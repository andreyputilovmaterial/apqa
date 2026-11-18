"""Tests for the pure (non-COM) helpers of the ``get-content-mdd`` cmdlet.

The actual COM/MDM reading path cannot be exercised here (it needs Windows,
MDM/Professional and pywin32), so these tests cover the arg-normalization,
value-coercion and category-map helpers that run everywhere.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.cmdlets.get_content_mdd import (  # noqa: E402
    _MDDReader,
    _as_int,
    _as_list,
    _category_map,
    _is_digit_name,
    _iter_attr,
    _plain,
    _safe_get,
    _safe_str_get,
    _str_safe,
)
from src.cmdlets.value_types import Collection  # noqa: E402


class _Stub:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def test_as_list():
    assert _as_list(None) == []
    assert _as_list('Question,Analysis') == ['Question', 'Analysis']
    assert _as_list('Question, Analysis , ENU') == ['Question', 'Analysis', 'ENU']
    assert _as_list(['Q', 'A']) == ['Q', 'A']
    assert _as_list(('Q', 'A')) == ['Q', 'A']
    assert _as_list('single') == ['single']
    assert _as_list(42) == [42]


def test_is_digit_name():
    assert _is_digit_name('1')
    assert _is_digit_name(' 12 ')
    assert _is_digit_name(None) is False
    assert _is_digit_name('abc') is False
    assert _is_digit_name('1a') is False


def test_plain_coercion():
    assert _plain(None) is None
    assert _plain('x') == 'x'
    assert _plain(5) == 5
    assert _plain(3.5) == 3.5
    assert _plain(True) is True
    assert _plain('5') == '5'
    assert _plain('3.5') == '3.5'


def test_as_int():
    assert _as_int(None) is None
    assert _as_int(5) == 5
    assert _as_int('5') == 5
    assert _as_int('x') is None


def test_str_safe():
    assert _str_safe(None) is None
    assert _str_safe('x') == 'x'
    assert _str_safe(42) == '42'


def test_safe_get_and_str_get():
    stub = _Stub(Name='Q1', Label=None)
    assert _safe_get(stub, 'Name') == 'Q1'
    assert _safe_get(stub, 'Missing') is None
    assert _safe_str_get(stub, 'Name') == 'Q1'
    assert _safe_str_get(stub, 'Label') is None
    assert _safe_str_get(stub, 'Missing') is None


def test_iter_attr():
    stub = _Stub(Elements=[1, 2, 3])
    assert list(_iter_attr(stub, 'Elements')) == [1, 2, 3]
    assert list(_iter_attr(stub, 'Missing')) == []


def test_category_map_indexes_leaves_and_nested_groups():
    categories = [
        {'Name': 'A', 'value': None},
        {
            'Name': 'Group',
            'value': [
                {'Name': 'B', 'value': None},
                {'Name': 'C', 'value': None},
            ],
        },
    ]
    mapped = _category_map(categories)
    assert set(mapped) == {'A', 'Group', 'B', 'C'}
    assert mapped['A']['value'] is None
    assert mapped['Group']['value'][0]['Name'] == 'B'
    assert mapped['B']['Name'] == 'B'


def test_block_field_stores_subfields_in_Fields_bucket(monkeypatch):
    subfields = {'Cluster': {'Name': 'Cluster'}}
    reader = _MDDReader.__new__(_MDDReader)
    monkeypatch.setattr(
        _MDDReader,
        '_read_item_meta',
        lambda self, item, attrs: {'Name': 'SnifferData'},
    )
    monkeypatch.setattr(
        _MDDReader,
        '_read_subfields',
        lambda self, field: subfields,
    )

    block = reader._read_block_field(_Stub(Name='SnifferData'))

    assert block['Name'] == 'SnifferData'
    assert block['Fields'] is subfields
    assert block['value'] is None


def test_read_category_collection_returns_named_collection(monkeypatch):
    reader = _MDDReader.__new__(_MDDReader)
    monkeypatch.setattr(
        reader, '_read_category',
        lambda cat: {'Name': cat.Name},
    )
    stub = _Stub(Elements=[_Stub(Name='A'), _Stub(Name='B')])

    result = reader._read_category_collection(stub)

    assert isinstance(result, Collection)
    assert result.names == ['A', 'B']
    assert result.by_name == {'A': 0, 'B': 1}
    assert result[1] == {'Name': 'B'}


def test_read_category_collection_flattens_references_into_named_collection(monkeypatch):
    reader = _MDDReader.__new__(_MDDReader)
    reader.step_into = True
    monkeypatch.setattr(
        reader, '_read_category',
        lambda cat: {'Name': cat.Name},
    )
    shared = _Stub(Elements=[_Stub(Name='X')])
    monkeypatch.setattr(
        reader, '_resolve_shared_list',
        lambda ref_name: shared,
    )
    stub = _Stub(
        Elements=[
            _Stub(Name='A'),
            _Stub(Name='Ref', IsReference=True, ReferenceName='SL'),
        ]
    )

    result = reader._read_category_collection(stub)

    assert isinstance(result, Collection)
    assert result.names == ['A', 'X']
    assert result.by_name == {'A': 0, 'X': 1}


def test_scalar_categorical_field_emits_value_collection(monkeypatch):
    reader = _MDDReader.__new__(_MDDReader)
    monkeypatch.setattr(
        _MDDReader, '_read_item_meta',
        lambda self, item, attrs: {'Name': 'Q1', '_Attrs': attrs},
    )
    monkeypatch.setattr(
        _MDDReader, '_scalar_attributes',
        lambda self, field, dt: {'DataType': dt},
    )
    monkeypatch.setattr(
        reader, '_read_category_collection',
        lambda field: Collection([{'Name': 'Yes'}], ['Yes']),
    )

    block = reader._read_scalar_field(_Stub(DataType=3))

    assert isinstance(block['value'], Collection)
    assert block['value'].names == ['Yes']
    assert block['Categories'] == {'Yes': {'Name': 'Yes'}}


def test_non_categorical_scalar_field_value_is_none(monkeypatch):
    reader = _MDDReader.__new__(_MDDReader)
    monkeypatch.setattr(
        _MDDReader, '_read_item_meta',
        lambda self, item, attrs: {'Name': 'Q1', '_Attrs': attrs},
    )
    monkeypatch.setattr(
        _MDDReader, '_scalar_attributes',
        lambda self, field, dt: {'DataType': dt},
    )

    block = reader._read_scalar_field(_Stub(DataType=0))

    assert block['value'] is None
    assert 'Categories' not in block

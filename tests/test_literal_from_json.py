"""Tests for the `literal-from-json` source reader."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from src.cmdlets import cmdlets
from src.cmdlets.sysmissing import sysmissing
from src.cmdlets.value_types import Collection


def _parse(raw):
    return cmdlets.get('literal-from-json')(None, {'value': raw})


def test_parses_object_into_block():
    parsed = _parse('{"a": 1, "b": [true, null]}')
    assert parsed == {'a': 1, 'b': [True, None]}
    assert isinstance(parsed['b'], Collection)


def test_parses_array_into_collection():
    parsed = _parse('[1, 2.5, "x", false]')
    assert isinstance(parsed, Collection)
    assert parsed == [1, 2.5, 'x', False]
    assert parsed.names == ['1', '2', '3', '4']


def test_parses_array():
    assert _parse('[1, 2.5, "x", false]') == [1, 2.5, 'x', False]


def test_parses_scalars():
    assert _parse('"hello"') == 'hello'
    assert _parse('42') == 42
    assert _parse('3.14') == 3.14
    assert _parse('true') == True
    assert _parse('false') == False
    assert _parse('null') is sysmissing


def test_ignores_piped_value():
    assert cmdlets.get('literal-from-json')('ignored', {'value': '1'}) == 1


def test_missing_value_raises():
    with pytest.raises(ValueError, match='literal-from-json'):
        cmdlets.get('literal-from-json')(None, {})


def test_invalid_json_raises_readable_error():
    with pytest.raises(ValueError, match='literal-from-json'):
        _parse('{not json')

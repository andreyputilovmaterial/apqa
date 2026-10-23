"""Tests for the cmdlet registry, built-in cmdlets, comparison ops, and sysmissing."""

import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from src.cmdlets import cmdlets, comparisons
from src.cmdlets.sysmissing import sysmissing, is_sysmissing


# ---- sysmissing -----------------------------------------------------------

def test_sysmissing_is_none():
    assert sysmissing is None
    assert is_sysmissing(None)
    assert not is_sysmissing(0)
    assert not is_sysmissing('')
    assert not is_sysmissing(False)
    assert not is_sysmissing([])
    assert not is_sysmissing({})


# ---- cmdlet registry ------------------------------------------------------

def test_registry_get_unknown_raises():
    with pytest.raises(KeyError):
        cmdlets.get('does-not-exist')


def test_registry_register_decorator():
    registry = type(cmdlets)()

    @registry.register('double')
    def double(value, args):
        return value * 2

    assert registry.get('double')(21, {}) == 42
    assert 'double' in registry.names()


# ---- built-in cmdlets -----------------------------------------------------

def test_literal_returns_value():
    assert cmdlets.get('literal')(None, {'value': 15}) == 15


def test_literal_requires_value():
    with pytest.raises(ValueError):
        cmdlets.get('literal')(None, {})


def test_count_counts_collection():
    assert cmdlets.get('count')([1, 2, 3], {}) == 3
    assert cmdlets.get('count')({'a': 1, 'b': 2}, {}) == 2


def test_count_rejects_non_countable():
    with pytest.raises(TypeError):
        cmdlets.get('count')(5, {})


def test_count_rejects_sysmissing():
    with pytest.raises(ValueError):
        cmdlets.get('count')(sysmissing, {})


# ---- comparison ops -------------------------------------------------------

def test_eq():
    assert comparisons.get('eq')(1, 1) is True
    assert comparisons.get('eq')(1, 2) is False


def test_eq_sysmissing_equals_only_sysmissing():
    assert comparisons.get('eq')(sysmissing, sysmissing) is True
    assert comparisons.get('eq')(sysmissing, 0) is False
    assert comparisons.get('eq')(sysmissing, []) is False
    assert comparisons.get('eq')(sysmissing, '') is False
    assert comparisons.get('eq')(sysmissing, False) is False


def test_eq_bool_is_distinct_from_numbers():
    assert comparisons.get('eq')(False, 0) is False
    assert comparisons.get('eq')(True, 1) is False
    assert comparisons.get('eq')(False, 0.0) is False
    assert comparisons.get('eq')(True, True) is True


def test_eq_int_and_float_unify():
    assert comparisons.get('eq')(1, 1.0) is True


def test_eq_numeric_text_coerces_to_number():
    assert comparisons.get('eq')('0', 0) is True
    assert comparisons.get('eq')('3.14', 3.14) is True
    assert comparisons.get('eq')(0, '0') is True


def test_eq_non_numeric_text_vs_number_is_false():
    assert comparisons.get('eq')('abc', 5) is False
    assert comparisons.get('eq')(5, 'abc') is False


def test_ne():
    assert comparisons.get('ne')(1, 2) is True
    assert comparisons.get('ne')(1, 1) is False
    assert comparisons.get('ne')(sysmissing, sysmissing) is False
    assert comparisons.get('ne')(sysmissing, 1) is True


def test_ordering():
    assert comparisons.get('lt')(1, 2) is True
    assert comparisons.get('le')(2, 2) is True
    assert comparisons.get('gt')(3, 2) is True
    assert comparisons.get('ge')(2, 2) is True


def test_ordering_with_sysmissing_is_false():
    assert comparisons.get('lt')(sysmissing, 1) is False
    assert comparisons.get('lt')(1, sysmissing) is False
    assert comparisons.get('gt')(sysmissing, 1) is False


def test_ordering_bool_is_false():
    assert comparisons.get('lt')(False, True) is False
    assert comparisons.get('gt')(True, False) is False


def test_ordering_numeric_text_coerces():
    assert comparisons.get('lt')('9', 10) is True
    assert comparisons.get('lt')('10', 9) is False


def test_date_comparison_uses_aware_datetimes():
    a = datetime(2020, 1, 1, tzinfo=timezone.utc)
    b = datetime(2020, 1, 2, tzinfo=timezone.utc)
    assert comparisons.get('lt')(a, b) is True
    assert comparisons.get('eq')(a, b) is False


def test_contains():
    assert comparisons.get('contains')('abc', 'b') is True
    assert comparisons.get('contains')([1, 2, 3], 2) is True
    assert comparisons.get('contains')('abc', 'z') is False


def test_contains_with_sysmissing_is_false():
    assert comparisons.get('contains')(sysmissing, 1) is False
    assert comparisons.get('contains')('abc', sysmissing) is False


def test_contains_non_containable_is_false():
    assert comparisons.get('contains')(5, 1) is False

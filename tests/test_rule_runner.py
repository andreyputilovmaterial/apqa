"""Tests for the top-level rule runner."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from src.rule_runner import run_rule
from src.db_processors.rule_base import Rule
from src.cmdlets.sysmissing import sysmissing


def _literal(value):
    return {'cmdlet': 'literal', 'args': {'value': value}}


def test_literal_eq_true():
    rule = {'left': [_literal(15)], 'op': 'eq', 'right': [_literal(15)]}
    assert run_rule(rule) is True


def test_literal_eq_false():
    rule = {'left': [_literal(15)], 'op': 'eq', 'right': [_literal(16)]}
    assert run_rule(rule) is False


def test_count_pipeline():
    rule = {
        'left': [_literal([1, 2, 3]), {'cmdlet': 'count'}],
        'op': 'eq',
        'right': [_literal(3)],
    }
    assert run_rule(rule) is True


def test_accepts_rule_object():
    rule = Rule(name='r', left=[_literal(1)], op='eq', right=[_literal(1)])
    assert run_rule(rule) is True


def test_sysmissing_eq_sysmissing():
    rule = {'left': [_literal(sysmissing)], 'op': 'eq', 'right': [_literal(sysmissing)]}
    assert run_rule(rule) is True


def test_sysmissing_eq_zero_is_false():
    rule = {'left': [_literal(sysmissing)], 'op': 'eq', 'right': [_literal(0)]}
    assert run_rule(rule) is False


def test_op_args_passed_to_eq():
    rule = {
        'left': [_literal([1, 2, 3])],
        'op': 'eq',
        'op_args': {'unordered_arrays': True},
        'right': [_literal([3, 1, 2])],
    }
    assert run_rule(rule) is True


def test_op_args_must_be_mapping():
    rule = {
        'left': [_literal(1)],
        'op': 'eq',
        'op_args': 'not-a-mapping',
        'right': [_literal(1)],
    }
    with pytest.raises(ValueError):
        run_rule(rule)


def test_eq_unordered_dedicated_op():
    rule = {
        'left': [_literal([1, 2, 3])],
        'op': 'eq-unordered',
        'right': [_literal([3, 1, 2])],
    }
    assert run_rule(rule) is True


def test_unknown_op_raises():
    rule = {'left': [_literal(1)], 'op': 'nope', 'right': [_literal(1)]}
    with pytest.raises(KeyError):
        run_rule(rule)


def test_unknown_cmdlet_raises():
    rule = {'left': [{'cmdlet': 'nope'}], 'op': 'eq', 'right': [_literal(1)]}
    with pytest.raises(KeyError):
        run_rule(rule)


def test_missing_op_raises():
    rule = {'left': [_literal(1)], 'right': [_literal(1)]}
    with pytest.raises(ValueError):
        run_rule(rule)


def test_non_mapping_rule_raises():
    with pytest.raises(ValueError):
        run_rule([1, 2, 3])


def test_non_list_side_raises():
    rule = {'left': 'not-a-list', 'op': 'eq', 'right': [_literal(1)]}
    with pytest.raises(ValueError):
        run_rule(rule)


def test_cmdlet_error_propagates():
    rule = {'left': [{'cmdlet': 'literal'}], 'op': 'eq', 'right': [_literal(1)]}
    with pytest.raises(ValueError):
        run_rule(rule)

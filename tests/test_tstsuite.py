"""Tests for the QC-rule pytest entry-point helpers."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from src.db_processors.rule_base import Rule
from src.tstsuite import (
    is_unfinished,
    load_case_params,
    markers_for,
    pytest_param_for,
    run_tst_case,
)


def _rule(markers):
    return Rule(name='r', meta={'markers': markers})


def _complete_rule(markers):
    literal = {'cmdlet': 'literal', 'args': {'value': 1}}
    return Rule(
        name='r',
        meta={'markers': markers},
        left=[literal],
        op='eq',
        right=[literal],
    )


def test_markers_for_normalizes_values():
    assert markers_for(_rule(['skip'])) == ['skip']
    assert markers_for(_rule('xfail')) == ['xfail']
    assert markers_for(_rule([])) == []
    assert markers_for(_rule(None)) == []


def test_skip_marker_becomes_skip_mark():
    param = pytest_param_for(_complete_rule(['skip']))
    assert param.id == 'r'
    assert any(m.name == 'skip' for m in param.marks)


def test_pytest_param_uses_rule_id_not_display_name():
    rule = Rule(name='Skip Me', meta={'markers': ['skip']})
    param = pytest_param_for(rule)
    assert param.id == 'skip-me'


def test_xfail_marker_becomes_xfail_mark():
    param = pytest_param_for(_complete_rule(['xfail']))
    assert any(m.name == 'xfail' for m in param.marks)


def test_no_markers_produce_no_marks():
    param = pytest_param_for(_complete_rule([]))
    assert list(param.marks) == []


def test_is_unfinished():
    assert is_unfinished(_rule([])) is True
    assert is_unfinished(_rule(['skip'])) is True
    assert is_unfinished(_complete_rule([])) is False


def test_unfinished_rule_becomes_skip_mark():
    param = pytest_param_for(_rule([]))
    assert any(m.name == 'skip' for m in param.marks)


def test_unfinished_takes_precedence_over_xfail():
    param = pytest_param_for(_rule(['xfail']))
    assert any(m.name == 'skip' for m in param.marks)
    assert not any(m.name == 'xfail' for m in param.marks)


def _lit(value):
    return {'cmdlet': 'literal', 'args': {'value': value}}


def test_run_tst_case_passes_on_true():
    rule = Rule(name='r', left=[_lit(1)], op='eq', right=[_lit(1)])
    assert run_tst_case(rule) is None


def test_run_tst_case_fails_on_false():
    rule = Rule(name='r', left=[_lit(1)], op='eq', right=[_lit(2)])
    with pytest.raises(AssertionError):
        run_tst_case(rule)


def test_load_case_params_from_yaml(tmp_path):
    db_file = tmp_path / 'projects.yaml'
    db_file.write_text(
        '\n'.join([
            '- name: skip-rule',
            '  meta:',
            '    markers: [skip]',
            '- name: normal-rule',
            '  left:',
            '    - cmdlet: literal',
            '      args:',
            '        value: 1',
            '  op: eq',
            '  right:',
            '    - cmdlet: literal',
            '      args:',
            '        value: 1',
        ]),
        encoding='utf-8',
    )

    params = list(load_case_params(str(db_file)))

    assert [p.id for p in params] == ['skip-rule', 'normal-rule']
    assert any(m.name == 'skip' for m in params[0].marks)
    assert list(params[1].marks) == []


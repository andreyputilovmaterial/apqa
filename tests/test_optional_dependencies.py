"""Tests for optional-dependency cmdlets and the "fail only when used" contract."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from src.cmdlets import cmdlets
from src.rule_runner import run_rule


def _openpyxl_installed():
    try:
        import openpyxl  # noqa: F401
    except Exception:
        return False
    return True


def test_optional_cmdlet_is_always_known():
    # Whether or not openpyxl is installed, the cmdlet is known (rules can
    # reference it); it may simply be unavailable for execution.
    assert 'get-content-excel' in cmdlets.names()


def test_get_content_excel_raises_readable_error_without_openpyxl():
    if _openpyxl_installed():
        pytest.skip('openpyxl is installed; the missing-dependency path cannot be exercised')
    with pytest.raises(ImportError) as exc_info:
        cmdlets.get('get-content-excel')(None, {'path': 'whatever.xlsx'})

    message = str(exc_info.value)
    assert 'get-content-excel' in message
    assert 'openpyxl' in message
    assert exc_info.value.__cause__ is not None


def test_run_rule_raises_for_missing_optional_dependency():
    if _openpyxl_installed():
        pytest.skip('openpyxl is installed; the missing-dependency path cannot be exercised')
    rule = {
        'name': 'uses-excel',
        'left': [{'cmdlet': 'get-content-excel', 'args': {'path': 'whatever.xlsx'}}],
        'op': 'eq',
        'right': [{'cmdlet': 'literal', 'args': {'value': 1}}],
    }
    with pytest.raises(ImportError):
        run_rule(rule)

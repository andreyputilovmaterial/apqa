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


def test_validate_xml_compatible_is_always_known():
    # xml.etree.ElementTree is stdlib, but the cmdlet still follows the optional
    # dependency pattern: it is always registered and only fails if the import is
    # genuinely unavailable.
    assert 'validate-xml-compatible' in cmdlets.names()


def test_optional_dependency_requirements_are_discoverable():
    # build.sh / run_init.* discover every src/cmdlets/**/requirements.txt; the
    # optional-dependency machinery depends on those files sitting next to their
    # cmdlet. A comment-only requirements.txt (stdlib dependency) still counts.
    cmdlets_dir = Path(__file__).resolve().parents[1] / 'src' / 'cmdlets'
    relative = {
        p.relative_to(cmdlets_dir).as_posix()
        for p in cmdlets_dir.glob('*/requirements.txt')
    }
    assert 'get_content_excel/requirements.txt' in relative
    assert 'validate_xml_compatible/requirements.txt' in relative


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

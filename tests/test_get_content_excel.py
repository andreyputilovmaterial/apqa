"""Tests for the `get-content-excel` source reader (block of sheets)."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

openpyxl = pytest.importorskip('openpyxl')

from src.cmdlets import cmdlets


def _read(args):
    return cmdlets.get('get-content-excel')(None, args)


def _write_two_sheets(path):
    workbook = openpyxl.Workbook()
    first = workbook.active
    first.title = 'Title Details'
    first.append(['B', 'C'])
    first.append(['alpha', 1])
    first.append(['beta', 2])

    second = workbook.create_sheet('Second')
    second.append(['Name'])
    second.append(['x'])
    workbook.save(path)
    return path


def test_returns_block_keyed_by_sheet_name(tmp_path):
    file = _write_two_sheets(tmp_path / 'book.xlsx')
    result = _read({'path': str(file)})
    assert result == {
        'Title Details': [{'B': 'alpha', 'C': 1}, {'B': 'beta', 'C': 2}],
        'Second': [{'Name': 'x'}],
    }


def test_sheet_order_is_preserved(tmp_path):
    file = _write_two_sheets(tmp_path / 'book.xlsx')
    result = _read({'path': str(file)})
    assert list(result) == ['Title Details', 'Second']


def test_empty_sheet_is_an_empty_array(tmp_path):
    workbook = openpyxl.Workbook()
    workbook.active.title = 'Blank'
    file = tmp_path / 'blank.xlsx'
    workbook.save(file)
    assert _read({'path': str(file)}) == {'Blank': []}


def test_sheet_with_only_header_is_an_empty_array(tmp_path):
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = 'Header Only'
    sheet.append(['A', 'B'])
    file = tmp_path / 'header.xlsx'
    workbook.save(file)
    assert _read({'path': str(file)}) == {'Header Only': []}


def test_missing_path_raises():
    with pytest.raises(ValueError, match='get-content-excel'):
        _read({})


def test_duplicate_and_empty_headers_are_deduplicated(tmp_path):
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = 'Sheet'
    sheet.append(['A', 'A', None])
    sheet.append([1, 2, 3])
    file = tmp_path / 'dup.xlsx'
    workbook.save(file)
    result = _read({'path': str(file)})
    assert list(result['Sheet'][0]) == ['A', 'A.1', 'C']


def test_metadata_has_only_path_arg():
    args = cmdlets.describe('get-content-excel')['args']
    assert [a['name'] for a in args] == ['path']

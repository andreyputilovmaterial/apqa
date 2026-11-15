"""Tests for the diagnostic-notes channel (``src/cmdlets/diagnostic.py``)."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.cmdlets.diagnostic import (
    Notes,
    collect_notes,
    current_notes,
    format_note,
    format_notes,
    format_path,
    record_note,
)


def test_format_path_identifier_chain():
    assert format_path(['fields', 'BrandAwareness', 'label']) == (
        'fields.BrandAwareness.label'
    )


def test_format_path_array_index():
    assert format_path(['pages', 'Q1', 'value', 2]) == 'pages.Q1.value[2]'


def test_format_path_quotes_non_identifier_keys():
    assert format_path([
        'pages', 'Q1', 'value', 2, 'categories', 'None of the above', 'label',
    ]) == "pages.Q1.value[2].categories['None of the above'].label"


def test_format_path_empty():
    assert format_path([]) == ''


def test_format_note_with_path():
    assert format_note({'path': ['fields', 'X', 'label'], 'message': 'bad &'}) == (
        'fields.X.label: bad &'
    )


def test_format_note_without_path():
    assert format_note({'message': 'boom'}) == 'boom'


def test_format_notes_bullets():
    notes = [
        {'path': ['a'], 'message': 'one'},
        {'path': ['b'], 'message': 'two'},
    ]
    assert format_notes(notes) == '- a: one\n- b: two'


def test_collect_notes_provides_isolated_notes():
    with collect_notes() as notes:
        record_note(['a'], 'inside')
        assert current_notes() is notes
        assert notes.items == [{'path': ['a'], 'message': 'inside'}]
    assert current_notes() is None


def test_record_note_is_noop_without_context():
    assert record_note(['a'], 'nothing') is None


def test_notes_note_stores_path_copy():
    notes = Notes()
    path = ['a']
    notes.note(path, 'm')
    path.append('b')
    assert notes.items[0]['path'] == ['a']

"""Tests for rule/group technical-id (slug) generation."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.db_processors.ids import ensure_unique, is_valid_id, make_slug, unique_slug


def test_make_slug_lowercases_and_hyphenates():
    assert make_slug('File Exists', fallback='rule') == 'file-exists'


def test_make_slug_strips_special_characters():
    assert make_slug('A, "quote" & (special)! name', fallback='rule') == 'a-quote-special-name'


def test_make_slug_collapses_multiple_separators():
    assert make_slug('  hello    world  ', fallback='rule') == 'hello-world'


def test_make_slug_folds_accents_to_ascii():
    assert make_slug('Café résumé', fallback='rule') == 'cafe-resume'


def test_make_slug_prefixes_a_leading_digit():
    assert make_slug('9002 counts', fallback='rule') == 'rule-9002-counts'


def test_make_slug_falls_back_when_no_ascii_letters_remain():
    assert make_slug('!!!', fallback='rule') == 'rule'
    assert make_slug('проверка', fallback='group') == 'group'


def test_make_slug_is_stable_for_an_already_valid_id():
    assert make_slug('wave69-counts-equal-9002', fallback='rule') == 'wave69-counts-equal-9002'


def test_unique_slug_appends_suffix_on_collision():
    existing = {'file-exists'}
    assert unique_slug('file exists', existing, fallback='rule') == 'file-exists-2'
    existing = {'file-exists', 'file-exists-2'}
    assert unique_slug('file exists', existing, fallback='rule') == 'file-exists-3'


def test_ensure_unique_preserves_exact_spelling():
    assert ensure_unique('MyRule', set()) == 'MyRule'
    assert ensure_unique('MyRule', {'MyRule'}) == 'MyRule-2'


def test_is_valid_id():
    assert is_valid_id('file-exists') is True
    assert is_valid_id('File-Exists') is True
    assert is_valid_id('a1-b2') is True
    assert is_valid_id('1abc') is False
    assert is_valid_id('-abc') is False
    assert is_valid_id('a b') is False
    assert is_valid_id('') is False
    assert is_valid_id(None) is False

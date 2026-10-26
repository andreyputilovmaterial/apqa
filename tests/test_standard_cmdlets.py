"""Tests for the standard scalar cmdlets (conversions, logical, bitwise, string)."""

import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from src.cmdlets import cmdlets
from src.cmdlets.sysmissing import sysmissing


def _literal(value):
    return {'cmdlet': 'literal', 'args': {'value': value}}


def _operands(*values):
    return {'operands': [[_literal(v)] for v in values]}


# ---- type conversions ------------------------------------------------------

def test_as_text():
    assert cmdlets.get('as-text')(sysmissing, {}) == ''
    assert cmdlets.get('as-text')('abc', {}) == 'abc'
    assert cmdlets.get('as-text')(42, {}) == '42'
    assert cmdlets.get('as-text')(3.14, {}) == '3.14'


def test_as_integer():
    assert cmdlets.get('as-integer')(42, {}) == 42
    assert cmdlets.get('as-integer')('42', {}) == 42
    assert cmdlets.get('as-integer')(3.9, {}) == 3


def test_as_integer_propagates_errors():
    with pytest.raises(ValueError):
        cmdlets.get('as-integer')('3.14', {})
    with pytest.raises(TypeError):
        cmdlets.get('as-integer')(sysmissing, {})


def test_as_real():
    assert cmdlets.get('as-real')('3.14', {}) == 3.14
    assert cmdlets.get('as-real')(42, {}) == 42.0


def test_as_boolean():
    b = cmdlets.get('as-boolean')
    assert b(sysmissing, {}) is False
    assert b('', {}) is False
    assert b([], {}) is False
    assert b({}, {}) is False
    assert b(0, {}) is False
    assert b('x', {}) is True
    assert b(1, {}) is True
    assert b([0], {}) is True


def test_as_path():
    assert cmdlets.get('as-path')('/tmp/x', {}) == Path('/tmp/x')


def test_as_path_propagates_errors():
    with pytest.raises(TypeError):
        cmdlets.get('as-path')(sysmissing, {})


def test_as_date_accepts_aware_datetime():
    aware = datetime(2025, 7, 15, 10, 0, tzinfo=timezone.utc)
    assert cmdlets.get('as-date')(aware, {}) == aware


def test_as_date_parses_iso_text_with_timezone():
    result = cmdlets.get('as-date')('2025-07-15T10:00:00Z', {})
    assert result == datetime(2025, 7, 15, 10, 0, tzinfo=timezone.utc)


def test_as_date_rejects_naive_datetime():
    with pytest.raises(ValueError):
        cmdlets.get('as-date')(datetime(2025, 7, 15, 10, 0), {})


def test_as_date_rejects_bare_date():
    with pytest.raises(ValueError):
        cmdlets.get('as-date')(date(2025, 7, 15), {})


def test_as_date_uses_tz_arg_for_naive_datetime():
    result = cmdlets.get('as-date')(
        datetime(2025, 7, 15, 10, 0), {'tz': 'Europe/Berlin'}
    )
    assert result.hour == 10
    assert result.tzinfo is not None


def test_as_date_uses_tz_arg_for_naive_text():
    result = cmdlets.get('as-date')(
        '2025-07-15T10:00:00', {'tz': '+02:00'}
    )
    assert result.utcoffset() == timedelta(hours=2)


def test_as_date_rejects_invalid_tz_arg():
    with pytest.raises(ValueError):
        cmdlets.get('as-date')(
            datetime(2025, 7, 15, 10, 0), {'tz': 'Not/AZone'}
        )


# ---- logical ---------------------------------------------------------------

def test_not():
    n = cmdlets.get('not')
    assert n(False, {}) is True
    assert n('', {}) is True
    assert n(sysmissing, {}) is True
    assert n(1, {}) is False


def test_and():
    a = cmdlets.get('and')
    assert a(None, _operands(True, 1, 'x')) is True
    assert a(None, _operands(True, 0)) is False
    assert a(None, _operands(True, sysmissing)) is False


def test_or():
    o = cmdlets.get('or')
    assert o(None, _operands(False, '', 2)) is True
    assert o(None, _operands(False, '', 0)) is False


def test_any():
    assert cmdlets.get('any')([0, '', 3], {}) is True
    assert cmdlets.get('any')([0, '', None], {}) is False


def test_all():
    assert cmdlets.get('all')([1, 'x'], {}) is True
    assert cmdlets.get('all')([1, ''], {}) is False


def test_any_and_all_require_array():
    with pytest.raises(TypeError):
        cmdlets.get('any')('abc', {})
    with pytest.raises(TypeError):
        cmdlets.get('all')(5, {})


# ---- bitwise ---------------------------------------------------------------

def test_bit_not():
    assert cmdlets.get('bit-not')(0, {}) == -1
    assert cmdlets.get('bit-not')(5, {}) == -6


def test_bit_and_or_xor():
    assert cmdlets.get('bit-and')(None, _operands(6, 3)) == 2
    assert cmdlets.get('bit-or')(None, _operands(4, 1)) == 5
    assert cmdlets.get('bit-xor')(None, _operands(6, 3)) == 5


def test_bitwise_rejects_non_integer():
    with pytest.raises(TypeError):
        cmdlets.get('bit-not')(True, {})
    with pytest.raises(TypeError):
        cmdlets.get('bit-and')(None, _operands(1, 1.5))


def test_bit_shifts():
    assert cmdlets.get('bit-lshift')(None, _operands(1, 3)) == 8
    assert cmdlets.get('bit-rshift')(None, _operands(8, 2)) == 2


# ---- string ----------------------------------------------------------------

def test_length():
    assert cmdlets.get('length')('hello', {}) == 5
    assert cmdlets.get('length')('', {}) == 0


def test_length_requires_text():
    with pytest.raises(TypeError):
        cmdlets.get('length')(5, {})


def test_matches_case_sensitive_default():
    assert cmdlets.get('matches')('hello world', {'pattern': 'world'}) is True
    assert cmdlets.get('matches')('hello world', {'pattern': 'World'}) is False


def test_matches_case_insensitive():
    m = cmdlets.get('matches')
    assert m('hello world', {'pattern': 'WORLD', 'case_insensitive': True}) is True


def test_matches_regex():
    m = cmdlets.get('matches')
    assert m('abc123', {'pattern': '^abc', 'regex': True}) is True
    assert m('abc', {'pattern': '^b', 'regex': True}) is False


def test_matches_requires_pattern():
    with pytest.raises(ValueError):
        cmdlets.get('matches')('abc', {})


# ---- text cleaning (markup -> plain text) -----------------------------------

def test_format_strip_html_removes_inline_tags():
    assert cmdlets.get('format-strip-html')('how <i>would</i> you rate...', {}) == \
        'how would you rate...'


def test_format_strip_html_preserves_plain_text():
    assert cmdlets.get('format-strip-html')('plain text, no tags', {}) == \
        'plain text, no tags'


def test_format_strip_html_decodes_entities():
    assert cmdlets.get('format-strip-html')('fish &amp; chips', {}) == 'fish & chips'


def test_format_strip_html_is_lenient_with_unbalanced_markup():
    assert cmdlets.get('format-strip-html')('a <b>bold', {}) == 'a bold'


def test_format_strip_html_leaves_math_operators_alone():
    assert cmdlets.get('format-strip-html')('x < 3 and y > 2', {}) == 'x < 3 and y > 2'


def test_format_strip_html_sysmissing_becomes_empty_string():
    assert cmdlets.get('format-strip-html')(sysmissing, {}) == ''


def test_format_strip_html_other_scalars_use_as_text():
    strip = cmdlets.get('format-strip-html')
    assert strip(42, {}) == '42'
    assert strip(3.14, {}) == '3.14'
    assert strip(True, {}) == 'True'
    assert strip(date(2025, 7, 15), {}) == '2025-07-15'
    assert strip(datetime(2025, 7, 15, 10, 0, tzinfo=timezone.utc), {}) == \
        '2025-07-15 10:00:00+00:00'
    assert strip(Path('/tmp/plain-name'), {}) == '/tmp/plain-name'


def test_format_strip_html_block_processes_fields_and_keeps_shape():
    assert cmdlets.get('format-strip-html')({
        'a': 'x <b>bold</b>',
        'b': 'plain',
        'c': 7,
    }, {}) == {'a': 'x bold', 'b': 'plain', 'c': '7'}


def test_format_strip_html_array_processes_items_and_keeps_shape():
    assert cmdlets.get('format-strip-html')(
        ['a <b>bold</b>', 'plain', None, 7],
        {},
    ) == ['a bold', 'plain', '', '7']


def test_format_strip_html_recurse_into_nested_compounds():
    assert cmdlets.get('format-strip-html')(
        [{'label': 'how <i>would</i> you rate...'}],
        {},
    ) == [{'label': 'how would you rate...'}]


def test_format_strip_html_empty_compounds_stay_empty():
    assert cmdlets.get('format-strip-html')({}, {}) == {}
    assert cmdlets.get('format-strip-html')([], {}) == []

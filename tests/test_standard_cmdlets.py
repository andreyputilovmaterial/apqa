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
    assert b(sysmissing, {}) == False
    assert b('', {}) == False
    assert b([], {}) == False
    assert b({}, {}) == False
    assert b(0, {}) == False
    assert b('x', {}) == True
    assert b(1, {}) == True
    assert b([0], {}) == True


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
    assert result.value.hour == 10
    assert result.value.tzinfo is not None


def test_as_date_uses_tz_arg_for_naive_text():
    result = cmdlets.get('as-date')(
        '2025-07-15T10:00:00', {'tz': '+02:00'}
    )
    assert result.value.utcoffset() == timedelta(hours=2)


def test_as_date_rejects_invalid_tz_arg():
    with pytest.raises(ValueError):
        cmdlets.get('as-date')(
            datetime(2025, 7, 15, 10, 0), {'tz': 'Not/AZone'}
        )


# ---- logical ---------------------------------------------------------------

def test_not():
    n = cmdlets.get('logical-not')
    assert n(False, {}) == True
    assert n('', {}) == True
    assert n(sysmissing, {}) == True
    assert n(1, {}) == False


def test_and():
    a = cmdlets.get('logical-and')
    assert a(None, _operands(True, 1, 'x')) == True
    assert a(None, _operands(True, 0)) == False
    assert a(None, _operands(True, sysmissing)) == False


def test_or():
    o = cmdlets.get('logical-or')
    assert o(None, _operands(False, '', 2)) == True
    assert o(None, _operands(False, '', 0)) == False


def test_any():
    assert cmdlets.get('logical-any')([0, '', 3], {}) == True
    assert cmdlets.get('logical-any')([0, '', None], {}) == False


def test_all():
    assert cmdlets.get('logical-all')([1, 'x'], {}) == True
    assert cmdlets.get('logical-all')([1, ''], {}) == False


def test_any_and_all_traverse_compound_trees():
    assert cmdlets.get('logical-all')({'a': [1, 2], 'b': {'c': 'x'}}, {}) == True
    assert cmdlets.get('logical-all')({'a': [1, 0], 'b': {'c': 'x'}}, {}) == False
    assert cmdlets.get('logical-any')({'a': [0, ''], 'b': {'c': 'x'}}, {}) == True
    assert cmdlets.get('logical-any')({'a': [0, ''], 'b': {'c': ''}}, {}) == False


def test_any_and_all_accept_scalar():
    assert cmdlets.get('logical-all')(5, {}) == True
    assert cmdlets.get('logical-all')('', {}) == False
    assert cmdlets.get('logical-any')(0, {}) == False
    assert cmdlets.get('logical-any')('abc', {}) == True


def test_any_and_all_empty_compounds():
    assert cmdlets.get('logical-all')([], {}) == True
    assert cmdlets.get('logical-all')({}, {}) == True
    assert cmdlets.get('logical-any')([], {}) == False
    assert cmdlets.get('logical-any')({}, {}) == False


# ---- logical (three-valued) -------------------------------------------------

def test_tristate_not():
    n = cmdlets.get('logical-tristate-not')
    assert n(False, {}) == True
    assert n(True, {}) == False
    assert n(sysmissing, {}) is sysmissing
    assert n('', {}) == True
    assert n(1, {}) == False


def test_tristate_and():
    a = cmdlets.get('logical-tristate-and')
    assert a(None, _operands(True, 1, 'x')) == True
    assert a(None, _operands(True, 0)) == False
    assert a(None, _operands(True, sysmissing)) is sysmissing
    assert a(None, _operands(True, 0, sysmissing)) == False


def test_tristate_or():
    o = cmdlets.get('logical-tristate-or')
    assert o(None, _operands(False, '', 2)) == True
    assert o(None, _operands(False, '', 0)) == False
    assert o(None, _operands(False, '', sysmissing)) is sysmissing
    assert o(None, _operands(False, '', 2, sysmissing)) == True


def test_tristate_any():
    assert cmdlets.get('logical-tristate-any')([0, '', 3], {}) == True
    assert cmdlets.get('logical-tristate-any')([0, '', None], {}) is sysmissing
    assert cmdlets.get('logical-tristate-any')([0, ''], {}) == False
    assert cmdlets.get('logical-tristate-any')([], {}) == False


def test_tristate_all():
    assert cmdlets.get('logical-tristate-all')([1, 'x'], {}) == True
    assert cmdlets.get('logical-tristate-all')([1, ''], {}) == False
    assert cmdlets.get('logical-tristate-all')([1, None], {}) is sysmissing
    assert cmdlets.get('logical-tristate-all')([1, '', None], {}) == False
    assert cmdlets.get('logical-tristate-all')([], {}) == True


def test_tristate_any_and_all_traverse_compound_trees():
    assert cmdlets.get('logical-tristate-all')({'a': [1, 2], 'b': {'c': 'x'}}, {}) == True
    assert cmdlets.get('logical-tristate-all')({'a': [1, 0], 'b': {'c': 'x'}}, {}) == False
    assert cmdlets.get('logical-tristate-all')({'a': [1, None], 'b': {'c': 'x'}}, {}) is sysmissing
    assert cmdlets.get('logical-tristate-any')({'a': [0, ''], 'b': {'c': 'x'}}, {}) == True
    assert cmdlets.get('logical-tristate-any')({'a': [0, ''], 'b': {'c': ''}}, {}) == False
    assert cmdlets.get('logical-tristate-any')({'a': [0, None], 'b': {'c': ''}}, {}) is sysmissing


def test_tristate_any_and_all_accept_scalar():
    assert cmdlets.get('logical-tristate-all')(5, {}) == True
    assert cmdlets.get('logical-tristate-all')('', {}) == False
    assert cmdlets.get('logical-tristate-all')(None, {}) is sysmissing
    assert cmdlets.get('logical-tristate-any')(0, {}) == False
    assert cmdlets.get('logical-tristate-any')('abc', {}) == True
    assert cmdlets.get('logical-tristate-any')(None, {}) is sysmissing


# ---- bitwise ---------------------------------------------------------------

def test_bit_not():
    assert cmdlets.get('bitwise-not')(0, {}) == -1
    assert cmdlets.get('bitwise-not')(5, {}) == -6


def test_bit_and_or_xor():
    assert cmdlets.get('bitwise-and')(None, _operands(6, 3)) == 2
    assert cmdlets.get('bitwise-or')(None, _operands(4, 1)) == 5
    assert cmdlets.get('bitwise-xor')(None, _operands(6, 3)) == 5


def test_bitwise_rejects_non_integer():
    with pytest.raises(TypeError):
        cmdlets.get('bitwise-not')(True, {})
    with pytest.raises(TypeError):
        cmdlets.get('bitwise-and')(None, _operands(1, 1.5))


def test_bit_shifts():
    assert cmdlets.get('bitwise-lshift')(None, _operands(1, 3)) == 8
    assert cmdlets.get('bitwise-rshift')(None, _operands(8, 2)) == 2


# ---- string ----------------------------------------------------------------

def test_transform_text_count_chars():
    assert cmdlets.get('transform-text-count-chars')('hello', {}) == 5
    assert cmdlets.get('transform-text-count-chars')('', {}) == 0


def test_transform_text_count_chars_strips_whitespace():
    assert cmdlets.get('transform-text-count-chars')(
        '  hello  ', {'strip_whitespace': True}
    ) == 5
    assert cmdlets.get('transform-text-count-chars')('  hello  ', {}) == 9


def test_transform_text_count_chars_requires_text():
    with pytest.raises(TypeError):
        cmdlets.get('transform-text-count-chars')(5, {})


def test_transform_text_regex_replaces_all_matches():
    assert cmdlets.get('transform-text-regex')(
        'abc 123 abc', {'pattern': 'abc', 'replacement': 'x'}
    ) == 'x 123 x'


def test_transform_text_regex_supports_backreferences():
    assert cmdlets.get('transform-text-regex')(
        'hello world', {'pattern': r'(\w+) (\w+)', 'replacement': r'\2 \1'}
    ) == 'world hello'


def test_transform_text_regex_empty_replacement_deletes_matches():
    assert cmdlets.get('transform-text-regex')(
        'a1b2c3', {'pattern': r'\d', 'replacement': ''}
    ) == 'abc'


def test_transform_text_regex_no_match_returns_original():
    assert cmdlets.get('transform-text-regex')(
        'hello', {'pattern': 'z', 'replacement': 'x'}
    ) == 'hello'


def test_transform_text_regex_case_insensitive():
    assert cmdlets.get('transform-text-regex')(
        'Hello hello',
        {'pattern': 'hello', 'replacement': 'hi', 'case_insensitive': True},
    ) == 'hi hi'


def test_transform_text_regex_count_limits_replacements():
    assert cmdlets.get('transform-text-regex')(
        'aaa', {'pattern': 'a', 'replacement': 'b', 'count': 2}
    ) == 'bba'


def test_transform_text_regex_count_zero_replaces_all():
    assert cmdlets.get('transform-text-regex')(
        'aaa', {'pattern': 'a', 'replacement': 'b', 'count': 0}
    ) == 'bbb'


def test_transform_text_regex_requires_text():
    with pytest.raises(TypeError):
        cmdlets.get('transform-text-regex')(5, {'pattern': 'x', 'replacement': 'y'})
    with pytest.raises(TypeError):
        cmdlets.get('transform-text-regex')(
            sysmissing, {'pattern': 'x', 'replacement': 'y'}
        )


def test_transform_text_regex_requires_pattern():
    with pytest.raises(ValueError):
        cmdlets.get('transform-text-regex')('abc', {'replacement': 'x'})
    with pytest.raises(ValueError):
        cmdlets.get('transform-text-regex')('abc', {'pattern': '', 'replacement': 'x'})


def test_transform_text_regex_requires_replacement():
    with pytest.raises(ValueError):
        cmdlets.get('transform-text-regex')('abc', {'pattern': 'a'})


def test_transform_text_regex_rejects_negative_count():
    with pytest.raises(ValueError):
        cmdlets.get('transform-text-regex')(
            'abc', {'pattern': 'a', 'replacement': 'x', 'count': -1}
        )


# ---- text code assignment grabbing -------------------------------------------

def test_transform_text_code_grab_assignments_mrs_grabs_basic_assignments():
    text = (
        "... something  \n"
        "   ProgramVersion = 4343 ' set Program Version  \n"
        " ...\n"
        ' ProgramVersion = "aaa"\n'
        " ... "
    )
    assert cmdlets.get('transform-text-code-grab-assignments-mrs')(
        text, {'variable_name': 'ProgramVersion'}
    ) == ['4343', '"aaa"']


def test_transform_text_code_grab_assignments_mrs_returns_a_collection_of_strings():
    result = cmdlets.get('transform-text-code-grab-assignments-mrs')(
        'ProgramVersion = 4343\n', {'variable_name': 'ProgramVersion'}
    )
    assert isinstance(result, list)
    assert result[0] == '4343'
    assert result[0].type_name == 'text'


def test_transform_text_code_grab_assignments_mrs_no_match_returns_empty():
    assert cmdlets.get('transform-text-code-grab-assignments-mrs')(
        'nothing relevant\n', {'variable_name': 'ProgramVersion'}
    ) == []


def test_transform_text_code_grab_assignments_mrs_ignores_other_variables():
    text = 'OtherVar = 1\nProgramVersion = 4343\n'
    assert cmdlets.get('transform-text-code-grab-assignments-mrs')(
        text, {'variable_name': 'ProgramVersion'}
    ) == ['4343']


def test_transform_text_code_grab_assignments_mrs_keeps_value_verbatim():
    # The captured group is returned as-is: quotes and inner spacing are kept.
    text = "ProgramVersion = \"aaa\" ' comment\nProgramVersion = 12 34\n"
    assert cmdlets.get('transform-text-code-grab-assignments-mrs')(
        text, {'variable_name': 'ProgramVersion'}
    ) == ['"aaa"', '12 34']


def test_transform_text_code_grab_assignments_mrs_handles_crlf():
    text = 'ProgramVersion = 4343\r\nProgramVersion = "aaa"\r\n'
    assert cmdlets.get('transform-text-code-grab-assignments-mrs')(
        text, {'variable_name': 'ProgramVersion'}
    ) == ['4343', '"aaa"']


def test_transform_text_code_grab_assignments_mrs_escapes_name_metacharacters():
    # The variable name is matched literally, so regex metacharacters do not act
    # as a pattern and a name like `a.b` only matches `a.b`.
    text = 'a.b = 1\naXb = 2\n'
    assert cmdlets.get('transform-text-code-grab-assignments-mrs')(
        text, {'variable_name': 'a.b'}
    ) == ['1']


def test_transform_text_code_grab_assignments_mrs_requires_text():
    with pytest.raises(TypeError):
        cmdlets.get('transform-text-code-grab-assignments-mrs')(
            5, {'variable_name': 'ProgramVersion'}
        )
    with pytest.raises(TypeError):
        cmdlets.get('transform-text-code-grab-assignments-mrs')(
            sysmissing, {'variable_name': 'ProgramVersion'}
        )


def test_transform_text_code_grab_assignments_mrs_requires_variable_name():
    with pytest.raises(ValueError):
        cmdlets.get('transform-text-code-grab-assignments-mrs')('x = 1', {})
    with pytest.raises(ValueError):
        cmdlets.get('transform-text-code-grab-assignments-mrs')(
            'x = 1', {'variable_name': ''}
        )


# ---- text cleaning (markup -> plain text) -----------------------------------

def test_transform_strip_html_removes_inline_tags():
    assert cmdlets.get('transform-strip-html')('how <i>would</i> you rate...', {}) == \
        'how would you rate...'


def test_transform_strip_html_preserves_plain_text():
    assert cmdlets.get('transform-strip-html')('plain text, no tags', {}) == \
        'plain text, no tags'


def test_transform_strip_html_decodes_entities():
    assert cmdlets.get('transform-strip-html')('fish &amp; chips', {}) == 'fish & chips'


def test_transform_strip_html_is_lenient_with_unbalanced_markup():
    assert cmdlets.get('transform-strip-html')('a <b>bold', {}) == 'a bold'


def test_transform_strip_html_leaves_math_operators_alone():
    assert cmdlets.get('transform-strip-html')('x < 3 and y > 2', {}) == 'x < 3 and y > 2'


def test_transform_strip_html_sysmissing_becomes_empty_string():
    assert cmdlets.get('transform-strip-html')(sysmissing, {}) == ''


def test_transform_strip_html_other_scalars_use_as_text():
    strip = cmdlets.get('transform-strip-html')
    assert strip(42, {}) == '42'
    assert strip(3.14, {}) == '3.14'
    assert strip(True, {}) == 'True'
    assert strip(date(2025, 7, 15), {}) == '2025-07-15'
    assert strip(datetime(2025, 7, 15, 10, 0, tzinfo=timezone.utc), {}) == \
        '2025-07-15 10:00:00+00:00'
    assert strip(Path('/tmp/plain-name'), {}) == '/tmp/plain-name'


def test_transform_strip_html_block_processes_fields_and_keeps_shape():
    assert cmdlets.get('transform-strip-html')({
        'a': 'x <b>bold</b>',
        'b': 'plain',
        'c': 7,
    }, {}) == {'a': 'x bold', 'b': 'plain', 'c': '7'}


def test_transform_strip_html_array_processes_items_and_keeps_shape():
    assert cmdlets.get('transform-strip-html')(
        ['a <b>bold</b>', 'plain', None, 7],
        {},
    ) == ['a bold', 'plain', '', '7']


def test_transform_strip_html_recurse_into_nested_compounds():
    assert cmdlets.get('transform-strip-html')(
        [{'label': 'how <i>would</i> you rate...'}],
        {},
    ) == [{'label': 'how would you rate...'}]


def test_transform_strip_html_empty_compounds_stay_empty():
    assert cmdlets.get('transform-strip-html')({}, {}) == {}
    assert cmdlets.get('transform-strip-html')([], {}) == []

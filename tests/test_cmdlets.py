"""Tests for the cmdlet registry, built-in cmdlets, comparison ops, and sysmissing."""

import sys
from datetime import date, datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from src.cmdlets import cmdlets, comparisons
from src.cmdlets.sysmissing import sysmissing, is_sysmissing


# ---- sysmissing -----------------------------------------------------------

def test_sysmissing_is_a_value_not_none():
    assert sysmissing is not None
    assert is_sysmissing(sysmissing)
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


def test_count_array_counts_iterations():
    assert cmdlets.get('count')([1, 2, 3], {}) == 3


def test_count_block_or_named_collection_counts_fields():
    assert cmdlets.get('count')({'a': 1, 'b': 2}, {}) == 2
    assert cmdlets.get('count')({'a': 1, 'b': 2, 'c': 3}, {}) == 3


def test_count_text():
    assert cmdlets.get('count')('hello', {}) == 1
    assert cmdlets.get('count')('', {}) == 0


def test_count_other_scalar_is_one_if_stored():
    assert cmdlets.get('count')(5, {}) == 1
    assert cmdlets.get('count')(True, {}) == 1
    assert cmdlets.get('count')(0, {}) == 1


def test_count_sysmissing_defaults_to_zero():
    assert cmdlets.get('count')(sysmissing, {}) == 0


def test_count_sysmissing_can_fail():
    with pytest.raises(ValueError):
        cmdlets.get('count')(sysmissing, {'fail_on_sysmissing': True})


def test_sort_scalars():
    assert cmdlets.get('sort')([3, 1, 2], {}) == [1, 2, 3]
    assert cmdlets.get('sort')([3, 1, 2], {'descending': True}) == [3, 2, 1]


def test_sort_blocks_by_field():
    rows = [{'state': 'B'}, {'state': 'A'}]
    assert cmdlets.get('sort')(rows, {'by': 'state'}) == [{'state': 'A'}, {'state': 'B'}]


def test_sort_blocks_requires_by():
    with pytest.raises(TypeError):
        cmdlets.get('sort')([{'state': 'A'}, {'state': 'B'}], {})


def test_sort_rejects_non_array():
    with pytest.raises(TypeError):
        cmdlets.get('sort')(5, {})


# ---- terminal validation cmdlets -------------------------------------------

def test_validate_xml_compatible_accepts_valid_text():
    validate = cmdlets.get('validate-xml-compatible')
    assert validate('hello', {}) == True
    assert validate('a <b>bold</b> text', {}) == True
    assert validate('fish &amp; chips', {}) == True


def test_validate_xml_compatible_rejects_unescaped_ampersand():
    assert cmdlets.get('validate-xml-compatible')('a & b', {}) == False


def test_validate_xml_compatible_rejects_unbalanced_markup():
    assert cmdlets.get('validate-xml-compatible')('a <b>bold', {}) == False


def test_validate_xml_compatible_non_string_scalars_pass():
    # Non-text scalars are not XML markup, so they are not validated (a path or a
    # date must never break XML validity just because of how it is spelled).
    validate = cmdlets.get('validate-xml-compatible')
    assert validate(42, {}) == True
    assert validate(3.14, {}) == True
    assert validate(True, {}) == True
    assert validate(False, {}) == True
    assert validate(date(2025, 7, 15), {}) == True
    assert validate(datetime(2025, 7, 15, 10, 0, tzinfo=timezone.utc), {}) == True
    assert validate(sysmissing, {}) == True
    assert validate(Path('/tmp/plain-name'), {}) == True
    assert validate(Path('/tmp/a&b'), {}) == True


def test_validate_xml_compatible_block_ands_fields():
    validate = cmdlets.get('validate-xml-compatible')
    assert validate({'a': 'ok', 'b': 'also ok'}, {}) == True
    assert validate({'a': 'ok', 'b': 'a & b'}, {}) == False


def test_validate_xml_compatible_array_ands_items():
    validate = cmdlets.get('validate-xml-compatible')
    assert validate(['ok', 'also ok'], {}) == True
    assert validate(['ok', 'a & b'], {}) == False


def test_validate_xml_compatible_empty_compound_is_vacuously_true():
    validate = cmdlets.get('validate-xml-compatible')
    assert validate({}, {}) == True
    assert validate([], {}) == True


def test_validate_xml_compatible_ands_nested_compounds_recursively():
    validate = cmdlets.get('validate-xml-compatible')
    assert validate([{'a': 'ok'}, {'b': 'nested & bad'}], {}) == False


def test_validate_xml_compatible_compound_of_non_strings_passes():
    validate = cmdlets.get('validate-xml-compatible')
    assert validate({'a': 1, 'b': Path('/tmp/x&y')}, {}) == True


def test_validate_text_matches_case_sensitive_default():
    validate = cmdlets.get('validate-text-matches')
    assert validate('hello world', {'pattern': 'world'}) == True
    assert validate('hello world', {'pattern': 'World'}) == False


def test_validate_text_matches_case_insensitive():
    validate = cmdlets.get('validate-text-matches')
    assert validate('hello world', {'pattern': 'WORLD', 'case_insensitive': True}) == True


def test_validate_text_matches_regex():
    validate = cmdlets.get('validate-text-matches')
    assert validate('abc123', {'pattern': '^abc', 'regex': True}) == True
    assert validate('abc', {'pattern': '^b', 'regex': True}) == False


def test_validate_text_matches_requires_pattern():
    with pytest.raises(ValueError):
        cmdlets.get('validate-text-matches')('abc', {})


def test_validate_text_matches_non_text_scalars_pass():
    validate = cmdlets.get('validate-text-matches')
    assert validate(42, {'pattern': 'x'}) == True
    assert validate(3.14, {'pattern': 'x'}) == True
    assert validate(True, {'pattern': 'x'}) == True
    assert validate(False, {'pattern': 'x'}) == True
    assert validate(date(2025, 7, 15), {'pattern': 'x'}) == True
    assert validate(datetime(2025, 7, 15, 10, 0, tzinfo=timezone.utc), {'pattern': 'x'}) == True
    assert validate(sysmissing, {'pattern': 'x'}) == True
    assert validate(Path('/tmp/plain-name'), {'pattern': 'x'}) == True


def test_validate_text_matches_block_ands_fields():
    validate = cmdlets.get('validate-text-matches')
    assert validate({'a': 'world', 'b': 'world'}, {'pattern': 'world'}) == True
    assert validate({'a': 'world', 'b': 'other'}, {'pattern': 'world'}) == False


def test_validate_text_matches_array_ands_items():
    validate = cmdlets.get('validate-text-matches')
    assert validate(['world', 'world'], {'pattern': 'world'}) == True
    assert validate(['world', 'other'], {'pattern': 'world'}) == False


def test_validate_text_matches_empty_compound_is_vacuously_true():
    validate = cmdlets.get('validate-text-matches')
    assert validate({}, {'pattern': 'x'}) == True
    assert validate([], {'pattern': 'x'}) == True


def test_validate_text_matches_ands_nested_compounds_recursively():
    validate = cmdlets.get('validate-text-matches')
    assert validate([{'a': 'world'}, {'b': 'nested world'}], {'pattern': 'world'}) == True
    assert validate([{'a': 'world'}, {'b': 'nested'}], {'pattern': 'world'}) == False


def test_validate_text_matches_compound_of_non_strings_passes():
    validate = cmdlets.get('validate-text-matches')
    assert validate({'a': 1, 'b': Path('/tmp/x')}, {'pattern': 'x'}) == True


def test_validate_text_matches_records_failed_path():
    from src.cmdlets.diagnostic import collect_notes

    validate = cmdlets.get('validate-text-matches')
    with collect_notes() as notes:
        assert validate({'a': 'world', 'b': 'nope'}, {'pattern': 'world'}) == False
    assert len(notes.items) == 1
    assert notes.items[0]['path'] == ['b']
    assert 'world' in notes.items[0]['message']


def test_validate_text_matches_records_array_index_path():
    from src.cmdlets.diagnostic import collect_notes

    validate = cmdlets.get('validate-text-matches')
    with collect_notes() as notes:
        assert validate(['world', 'nope'], {'pattern': 'world'}) == False
    assert len(notes.items) == 1
    assert notes.items[0]['path'] == [1]
    assert 'world' in notes.items[0]['message']


# ---- terminal predicate cmdlets --------------------------------------------

def test_is_sysmissing_true_for_none():
    assert cmdlets.get('is-sysmissing')(sysmissing, {}) == True


def test_is_sysmissing_false_for_empty_string():
    assert cmdlets.get('is-sysmissing')('', {}) == False


def test_is_sysmissing_false_for_zero_and_false():
    assert cmdlets.get('is-sysmissing')(0, {}) == False
    assert cmdlets.get('is-sysmissing')(False, {}) == False


def test_is_sysmissing_false_for_empty_compounds():
    assert cmdlets.get('is-sysmissing')({}, {}) == False
    assert cmdlets.get('is-sysmissing')([], {}) == False


def test_is_sysmissing_false_for_compound_of_sysmissing_fields():
    assert cmdlets.get('is-sysmissing')({'a': sysmissing}, {}) == False
    assert cmdlets.get('is-sysmissing')([sysmissing, sysmissing], {}) == False


def test_is_sysmissing_false_for_any_other_value():
    assert cmdlets.get('is-sysmissing')('hello', {}) == False
    assert cmdlets.get('is-sysmissing')(5, {}) == False
    assert cmdlets.get('is-sysmissing')(True, {}) == False


# ---- comparison ops -------------------------------------------------------

def test_eq():
    assert comparisons.get('cmp-eq')(1, 1) == True
    assert comparisons.get('cmp-eq')(1, 2) == False


def test_eq_sysmissing_equals_only_sysmissing():
    assert comparisons.get('cmp-eq')(sysmissing, sysmissing) == True
    assert comparisons.get('cmp-eq')(sysmissing, 0) == False
    assert comparisons.get('cmp-eq')(sysmissing, []) == False
    assert comparisons.get('cmp-eq')(sysmissing, '') == False
    assert comparisons.get('cmp-eq')(sysmissing, False) == False


def test_eq_bool_is_distinct_from_numbers():
    assert comparisons.get('cmp-eq')(False, 0) == False
    assert comparisons.get('cmp-eq')(True, 1) == False
    assert comparisons.get('cmp-eq')(False, 0.0) == False
    assert comparisons.get('cmp-eq')(True, True) == True


def test_eq_int_and_float_unify():
    assert comparisons.get('cmp-eq')(1, 1.0) == True


def test_eq_numeric_text_coerces_to_number():
    assert comparisons.get('cmp-eq')('0', 0) == True
    assert comparisons.get('cmp-eq')('3.14', 3.14) == True
    assert comparisons.get('cmp-eq')(0, '0') == True


def test_eq_non_numeric_text_vs_number_is_false():
    assert comparisons.get('cmp-eq')('abc', 5) == False
    assert comparisons.get('cmp-eq')(5, 'abc') == False


def test_eq_blocks_are_order_insensitive():
    a = {'Name': 'x', 'FullName': 'y'}
    b = {'FullName': 'y', 'Name': 'x'}
    assert comparisons.get('cmp-eq')(a, b) == True


def test_eq_blocks_compare_by_name():
    a = {'Name': 'x', 'FullName': 'y'}
    b = {'Name': 'x', 'FullName': 'z'}
    assert comparisons.get('cmp-eq')(a, b) == False


def test_eq_blocks_apply_scalar_rules_to_fields():
    # bool vs number must stay distinct even when nested.
    assert comparisons.get('cmp-eq')({'flag': True}, {'flag': 1}) == False


def test_eq_arrays_are_strict_order():
    assert comparisons.get('cmp-eq')([1, 2], [1, 2]) == True
    assert comparisons.get('cmp-eq')([1, 2], [2, 1]) == False


def test_eq_arrays_recurse_into_blocks():
    a = [{'n': 1}, {'n': 2}]
    b = [{'n': 2}, {'n': 1}]
    assert comparisons.get('cmp-eq')(a, b) == False


def test_eq_mixed_compound_kinds_are_not_equal():
    assert comparisons.get('cmp-eq')({'a': 1}, [1]) == False
    assert comparisons.get('cmp-eq')([1], 1) == False


def test_ne_compound():
    assert comparisons.get('cmp-ne')([1, 2], [2, 1]) == True
    assert comparisons.get('cmp-ne')({'a': 1}, {'a': 1}) == False


def test_ordering_on_compound_is_false():
    assert comparisons.get('cmp-lt')([1, 2], [1, 3]) == False
    assert comparisons.get('cmp-gt')({'a': 1}, {'a': 0}) == False


def test_eq_unordered_arrays_arg():
    eq = comparisons.get('cmp-eq')
    assert eq([1, 2, 3], [3, 1, 2]) == False
    assert eq([1, 2, 3], [3, 1, 2], {'unordered_arrays': True}) == True


def test_eq_unordered_arrays_is_multiset():
    eq = comparisons.get('cmp-eq')
    assert eq([1, 1, 2], [1, 2, 1], {'unordered_arrays': True}) == True
    assert eq([1, 1, 2], [1, 2, 2], {'unordered_arrays': True}) == False


def test_eq_unordered_recurses_into_blocks():
    eq = comparisons.get('cmp-eq')
    a = [{'n': 1}, {'n': 2}]
    b = [{'n': 2}, {'n': 1}]
    assert eq(a, b) == False
    assert eq(a, b, {'unordered_arrays': True}) == True


def test_eq_unordered_op():
    eq_unordered = comparisons.get('cmp-eq-unordered')
    assert eq_unordered([1, 2, 3], [3, 2, 1]) == True
    assert eq_unordered([1, 2], [1, 3]) == False


def test_ne():
    assert comparisons.get('cmp-ne')(1, 2) == True
    assert comparisons.get('cmp-ne')(1, 1) == False
    assert comparisons.get('cmp-ne')(sysmissing, sysmissing) == False
    assert comparisons.get('cmp-ne')(sysmissing, 1) == True


def test_ordering():
    assert comparisons.get('cmp-lt')(1, 2) == True
    assert comparisons.get('cmp-le')(2, 2) == True
    assert comparisons.get('cmp-gt')(3, 2) == True
    assert comparisons.get('cmp-ge')(2, 2) == True


def test_ordering_with_sysmissing_is_false():
    assert comparisons.get('cmp-lt')(sysmissing, 1) == False
    assert comparisons.get('cmp-lt')(1, sysmissing) == False
    assert comparisons.get('cmp-gt')(sysmissing, 1) == False


def test_ordering_bool_is_false():
    assert comparisons.get('cmp-lt')(False, True) == False
    assert comparisons.get('cmp-gt')(True, False) == False


def test_ordering_numeric_text_coerces():
    assert comparisons.get('cmp-lt')('9', 10) == True
    assert comparisons.get('cmp-lt')('10', 9) == False


def test_date_comparison_uses_aware_datetimes():
    a = datetime(2020, 1, 1, tzinfo=timezone.utc)
    b = datetime(2020, 1, 2, tzinfo=timezone.utc)
    assert comparisons.get('cmp-lt')(a, b) == True
    assert comparisons.get('cmp-eq')(a, b) == False


def test_contains():
    assert comparisons.get('cmp-contains')('abc', 'b') == True
    assert comparisons.get('cmp-contains')([1, 2, 3], 2) == True
    assert comparisons.get('cmp-contains')('abc', 'z') == False


def test_contains_with_sysmissing_is_false():
    assert comparisons.get('cmp-contains')(sysmissing, 1) == False
    assert comparisons.get('cmp-contains')('abc', sysmissing) == False


def test_contains_non_containable_is_false():
    assert comparisons.get('cmp-contains')(5, 1) == False

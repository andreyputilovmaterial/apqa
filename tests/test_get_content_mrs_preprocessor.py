"""Tests for the `get-content-mrs-preprocessor` source reader."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from src.cmdlets import cmdlets


def _run(path, **extra):
    return cmdlets.get('get-content-mrs-preprocessor')(None, {'path': str(path), **extra})


def _write(directory, name, text):
    file = directory / name
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(text, encoding='utf-8')
    return file


def test_example_definitions(tmp_path):
    file = _write(tmp_path, 'main.c', '#define A "bbb"\n#define B 3\n#define C A\n')
    result = _run(file)
    assert result == {'A': '"bbb"', 'B': '3', 'C': '"bbb"'}


def test_definitions_are_stored_as_verbatim_text(tmp_path):
    # The preprocessor is intentionally dumb: it does not interpret the meaning
    # of a stored body, so a numeric-looking definition stays text.
    file = _write(tmp_path, 'main.c', '#define A "bbb"\n#define B 3\n#define C A\n')
    result = _run(file)
    assert result['A'].type_name == 'text'
    assert result['B'].type_name == 'text'
    assert result['B'].value == '3'
    assert result['C'].value == '"bbb"'


def test_missing_path_arg_raises():
    with pytest.raises(ValueError, match='missing required arg'):
        cmdlets.get('get-content-mrs-preprocessor')(None, {})


def test_file_not_found_raises(tmp_path):
    missing = tmp_path / 'nope.c'
    with pytest.raises(FileNotFoundError):
        _run(missing)


def test_include_merges_definitions_from_current_dir(tmp_path):
    _write(tmp_path, 'inc.h', '#define FROM_INC 42\n')
    main = _write(tmp_path, 'main.c', '#include "inc.h"\n#define MAIN yes\n')
    result = _run(main, current_dir=str(tmp_path))
    assert result == {'FROM_INC': '42', 'MAIN': 'yes'}


def test_include_defaults_to_starting_file_directory(tmp_path):
    _write(tmp_path, 'inc.h', '#define FROM_INC 42\n')
    main = _write(tmp_path, 'main.c', '#include "inc.h"\n')
    assert _run(main) == {'FROM_INC': '42'}


def test_include_with_angle_brackets(tmp_path):
    _write(tmp_path, 'inc.h', '#define FROM_INC 42\n')
    main = _write(tmp_path, 'main.c', '#include <inc.h>\n')
    assert _run(main) == {'FROM_INC': '42'}


def test_utf8_bom_in_main_file_is_stripped(tmp_path):
    file = tmp_path / 'bom.c'
    file.write_bytes(b'\xef\xbb\xbf#define A 1\n#define B "bbb"\n')
    assert _run(file) == {'A': '1', 'B': '"bbb"'}


def test_utf8_bom_in_included_file_is_stripped(tmp_path):
    (tmp_path / 'inc.h').write_bytes(b'\xef\xbb\xbf#define FROM_INC 42\n')
    main = _write(tmp_path, 'main.c', '#include "inc.h"\n#define MAIN yes\n')
    assert _run(main) == {'FROM_INC': '42', 'MAIN': 'yes'}


@pytest.mark.parametrize(
    'bom, encoding',
    [
        (b'\xff\xfe', 'utf-16-le'),
        (b'\xfe\xff', 'utf-16-be'),
        (b'\xff\xfe\x00\x00', 'utf-32-le'),
        (b'\x00\x00\xfe\xff', 'utf-32-be'),
    ],
)
def test_utf16_and_utf32_boms_are_decoded(tmp_path, bom, encoding):
    file = tmp_path / f'{encoding}.c'
    file.write_bytes(bom + '#define A 1\n#define B "bbb"\n'.encode(encoding))
    assert _run(file) == {'A': '1', 'B': '"bbb"'}


def test_utf16_le_bom_in_included_file_is_decoded(tmp_path):
    (tmp_path / 'inc.h').write_bytes(
        b'\xff\xfe' + '#define FROM_INC 42\n'.encode('utf-16-le')
    )
    main = _write(tmp_path, 'main.c', '#include "inc.h"\n#define MAIN yes\n')
    assert _run(main) == {'FROM_INC': '42', 'MAIN': 'yes'}


def test_include_unresolved_raises(tmp_path):
    main = _write(tmp_path, 'main.c', '#include "missing.h"\n')
    with pytest.raises(FileNotFoundError, match='missing.h'):
        _run(main)


def test_recursive_include_raises(tmp_path):
    main = _write(tmp_path, 'main.c', '#include "main.c"\n')
    with pytest.raises(ValueError, match='recursive #include'):
        _run(main)


def test_ifdef_and_ifndef(tmp_path):
    main = _write(
        tmp_path,
        'main.c',
        '#ifndef GUARD\n#define GUARD 1\n#endif\n'
        '#ifdef GUARD\n#define ENABLED yes\n#endif\n',
    )
    assert _run(main) == {'GUARD': '1', 'ENABLED': 'yes'}


def test_if_defined_paren_and_bare(tmp_path):
    main = _write(
        tmp_path,
        'main.c',
        '#define A 1\n'
        '#if defined(A)\n#define B 2\n#endif\n'
        '#if defined C\n#define D 3\n#endif\n',
    )
    result = _run(main)
    assert result == {'A': '1', 'B': '2'}


def test_if_arithmetic(tmp_path):
    main = _write(
        tmp_path,
        'main.c',
        '#if 2 + 3 * 4 == 14\n#define OK yes\n#endif\n'
        '#if (10 / 3) == 3\n#define DIV yes\n#endif\n'
        '#if 7 % 4 == 3 && !0\n#define MOD yes\n#endif\n',
    )
    assert _run(main) == {'OK': 'yes', 'DIV': 'yes', 'MOD': 'yes'}


def test_elif_else_branching(tmp_path):
    main = _write(
        tmp_path,
        'main.c',
        '#if 0\n#define A 1\n#elif 1\n#define B 2\n#else\n#define C 3\n#endif\n',
    )
    assert _run(main) == {'B': '2'}


def test_case_insensitive_switch(tmp_path):
    main = _write(
        tmp_path,
        'main.c',
        '#define FOO 1\n#if defined(foo)\n#define BAR FOO\n#endif\n',
    )
    assert _run(main, case_insensitive=True) == {'foo': '1', 'bar': '1'}


def test_case_sensitive_by_default(tmp_path):
    main = _write(
        tmp_path,
        'main.c',
        '#define FOO 1\n#if defined(foo)\n#define BAR 2\n#endif\n',
    )
    assert _run(main) == {'FOO': '1'}


def test_forward_reference_resolved(tmp_path):
    # A few iterations of substitution are applied over the whole dictionary, so
    # a definition can reference another definition that appears later.
    main = _write(tmp_path, 'main.c', '#define A B\n#define B 3\n')
    assert _run(main) == {'A': '3', 'B': '3'}


def test_unknown_directives_are_ignored(tmp_path):
    main = _write(
        tmp_path,
        'main.c',
        '#pragma once\n#define A 1\n#undef A\n#warning something\n',
    )
    assert _run(main) == {'A': '1'}


def test_self_reference_is_stable(tmp_path):
    main = _write(tmp_path, 'main.c', '#define A A\n')
    assert _run(main) == {'A': 'A'}


def test_nested_conditional_inside_active_branch(tmp_path):
    main = _write(
        tmp_path,
        'main.c',
        '#if 1\n#if 1\n#define INNER yes\n#endif\n#endif\n',
    )
    assert _run(main) == {'INNER': 'yes'}


def test_include_inside_active_conditional(tmp_path):
    _write(tmp_path, 'inc.h', '#define FROM_INC 1\n')
    main = _write(tmp_path, 'main.c', '#if 1\n#include "inc.h"\n#endif\n')
    assert _run(main) == {'FROM_INC': '1'}


def test_macro_used_in_arithmetic_condition(tmp_path):
    main = _write(
        tmp_path,
        'main.c',
        '#define N 4\n#if N * 2 == 8\n#define OK yes\n#endif\n',
    )
    assert _run(main) == {'N': '4', 'OK': 'yes'}


def test_else_branch_chosen_when_if_false(tmp_path):
    main = _write(
        tmp_path,
        'main.c',
        '#if 0\n#define A 1\n#else\n#define B 2\n#endif\n',
    )
    assert _run(main) == {'B': '2'}


def test_elif_chain_picks_only_the_true_branch(tmp_path):
    main = _write(
        tmp_path,
        'main.c',
        '#if 0\n#define A 1\n#elif 0\n#define B 2\n#elif 1\n#define C 3\n#endif\n',
    )
    assert _run(main) == {'C': '3'}


def test_negated_defined(tmp_path):
    main = _write(
        tmp_path,
        'main.c',
        '#define X 1\n#if !defined(X)\n#define NO 1\n#else\n#define YES 2\n#endif\n',
    )
    assert _run(main) == {'X': '1', 'YES': '2'}


def test_metadata_args():
    meta = cmdlets.describe('get-content-mrs-preprocessor')
    assert meta['kind'] == 'source'
    assert 'filesystem' in meta['permissions']
    args = {a['name']: a for a in meta['args']}
    assert list(args) == ['path', 'current_dir', 'case_insensitive']
    assert args['path']['required'] is True
    assert args['path']['type'] == 'path'
    assert args['current_dir']['required'] is False
    assert args['current_dir']['type'] == 'path'
    assert args['case_insensitive']['type'] == 'boolean'
    assert args['case_insensitive']['default'] is False

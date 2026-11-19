"""`get-content-mrs-preprocessor` — run a small C-style preprocessor over a file.

Source reader: the piped value is ignored and the file is read from ``args``.

The preprocessor is deliberately dumb: it only does a few iterations of
identifier substitution and stores the resulting definitions in a block, without
trying to understand what any stored value *means*. Every definition body is
kept as verbatim text (quotes, numbers, … stay exactly as written after
substitution), so ``#define B 3`` stores the *text* ``"3"``, not an integer.

Supported directives (each is only recognised at the start of a line, after
optional whitespace):

    #define NAME body        object-like macro
    #include "path"          include another file (path resolved against
                             ``current_dir``; default = the starting file's dir)
    #include <path>
    #if EXPR                conditional
    #elif EXPR
    #else
    #endif
    #ifdef NAME / #ifndef NAME

``EXPR`` supports ``defined(NAME)`` / ``defined NAME``, the comparison operators
``== != < <= > >=``, the logical operators ``&& || !``, and basic integer
arithmetic (``+ - * / %``, parentheses). Undefined identifiers in a condition
evaluate to ``0`` (C semantics); string comparison is not supported.

Anything else — normal code lines, unknown directives such as ``#pragma`` /
``#undef``, function-like macros, recursion — is ignored or handled best-effort.
Substitution is purely textual, so a macro name inside a quoted string is also
replaced. Missing include files and recursive includes fail loudly.

Files are decoded by their byte-order mark (BOM): UTF-8, UTF-16 LE/BE and
UTF-32 LE/BE are recognised, the BOM is stripped, and the remaining bytes are
decoded with the matching codec. A file with no BOM is read as UTF-8.
"""

import re
from pathlib import Path

from ..registry import cmdlets
from ..value_types import Block, PipeValue

_IDENTIFIER = r'[A-Za-z_][A-Za-z0-9_]*'
_MAX_PASSES = 100
# BOM → codec for the *remaining* bytes (the BOM itself is stripped before
# decoding). Order matters: UTF-32 BOMs must be checked before UTF-16, because
# a UTF-32 LE BOM (FF FE 00 00) starts with a UTF-16 LE BOM (FF FE).
_BOMS = (
    (b'\x00\x00\xfe\xff', 'utf-32-be'),
    (b'\xff\xfe\x00\x00', 'utf-32-le'),
    (b'\xfe\xff', 'utf-16-be'),
    (b'\xff\xfe', 'utf-16-le'),
    (b'\xef\xbb\xbf', 'utf-8'),
)


def _decode_text(data, description):
    """Decode ``data`` honouring a leading BOM; no BOM falls back to UTF-8."""
    for bom, encoding in _BOMS:
        if data.startswith(bom):
            try:
                return data[len(bom):].decode(encoding)
            except UnicodeDecodeError as error:
                raise ValueError(
                    f'get-content-mrs-preprocessor: cannot decode {description} '
                    f'as {encoding}'
                ) from error
    try:
        return data.decode('utf-8')
    except UnicodeDecodeError as error:
        raise ValueError(
            f'get-content-mrs-preprocessor: cannot decode {description} as UTF-8'
        ) from error


def _read_text(path, description):
    return _decode_text(path.read_bytes(), description)

ARGS = [
    {
        'name': 'path',
        'type': 'path',
        'required': True,
        'description': 'Full path to the source file to preprocess.',
    },
    {
        'name': 'current_dir',
        'type': 'path',
        'required': False,
        'description': (
            'Root directory used to resolve #include paths; defaults to the '
            'directory containing the starting file.'
        ),
    },
    {
        'name': 'case_insensitive',
        'type': 'boolean',
        'required': False,
        'default': False,
        'description': 'Match identifiers case-insensitively.',
    },
]


@cmdlets.register(
    'get-content-mrs-preprocessor',
    kind='source',
    help='Run a small C-style preprocessor over a file and return its definitions as a block.',
    args=ARGS,
    permissions=['filesystem'],
    compact=[
        {'text': '[pre]', 'role': 'logo'},
        {'arg': 'path'},
    ],
)
def get_content_mrs_preprocessor(value: PipeValue, args: dict) -> Block:
    path = args.get('path')
    if not path:
        raise ValueError("get-content-mrs-preprocessor: missing required arg 'path'")

    case_insensitive = bool(args.get('case_insensitive', False))

    start_path = Path(path).expanduser().resolve()
    text = _read_text(start_path, f'{str(start_path)!r}')

    current_dir = args.get('current_dir')
    include_root = (
        Path(current_dir).expanduser().resolve() if current_dir else start_path.parent
    )

    ctx = {
        'definitions': {},
        'case_insensitive': case_insensitive,
        'include_root': include_root,
        'include_stack': [start_path],
    }

    _process(text.splitlines(), 0, ctx, frozenset())
    return Block(_expand_all(ctx['definitions'], case_insensitive))


# ---- identifier / directive helpers -----------------------------------------


def _canonical(name, case_insensitive):
    return name.lower() if case_insensitive else name


def _is_defined(name, ctx):
    return _canonical(name, ctx['case_insensitive']) in ctx['definitions']


_DIRECTIVE_RE = re.compile(r'^\s*#\s*(' + _IDENTIFIER + r')\s*(.*)$')


def _parse_directive(line):
    """Return ``(name, rest)`` for a directive line, or ``None``."""
    match = _DIRECTIVE_RE.match(line)
    if not match:
        return None
    return match.group(1), match.group(2)


_DEFINE_RE = re.compile(r'^(' + _IDENTIFIER + r')\s*(.*)$')


def _define(rest, ctx):
    match = _DEFINE_RE.match(rest)
    if not match:
        raise ValueError(f'get-content-mrs-preprocessor: malformed #define {rest!r}')
    name = match.group(1)
    body = match.group(2).strip()
    ctx['definitions'][_canonical(name, ctx['case_insensitive'])] = body


def _parse_include_path(rest):
    text = rest.strip()
    if len(text) >= 2 and text[0] == '"' and text[-1] == '"':
        return text[1:-1]
    if len(text) >= 2 and text[0] == '<' and text[-1] == '>':
        return text[1:-1]
    raise ValueError(f'get-content-mrs-preprocessor: malformed #include {rest!r}')


def _resolve_include(target, include_root):
    path = Path(target).expanduser()
    if not path.is_absolute():
        path = include_root / path
    return path.resolve()


def _include(rest, ctx):
    target = _parse_include_path(rest)
    resolved = _resolve_include(target, ctx['include_root'])

    if resolved in ctx['include_stack']:
        chain = ' -> '.join(str(p) for p in ctx['include_stack'] + [resolved])
        raise ValueError(
            f'get-content-mrs-preprocessor: recursive #include of {target!r}: {chain}'
        )

    try:
        text = _read_text(resolved, f'include {str(resolved)!r}')
    except FileNotFoundError:
        raise FileNotFoundError(
            f'get-content-mrs-preprocessor: cannot resolve #include {target!r} '
            f'(included from {str(ctx["include_stack"][-1])})'
        ) from None

    ctx['include_stack'].append(resolved)
    try:
        _process(text.splitlines(), 0, ctx, frozenset())
    finally:
        ctx['include_stack'].pop()


# ---- line processing --------------------------------------------------------


def _process(lines, pos, ctx, stops):
    """Process directives until a directive in ``stops`` (or EOF).

    Returns ``(pos, name, rest)`` when stopped at a ``stops`` directive, or just
    ``pos`` at EOF. Nested conditionals are consumed entirely here, so a
    ``#elif`` / ``#else`` / ``#endif`` returned by this function is always the
    caller's own branch terminator.
    """
    while pos < len(lines):
        parsed = _parse_directive(lines[pos])
        if parsed is None:
            pos += 1
            continue
        name, rest = parsed

        if name in stops:
            return pos, name, rest
        if name == 'define':
            _define(rest, ctx)
            pos += 1
        elif name == 'include':
            _include(rest, ctx)
            pos += 1
        elif name == 'if':
            pos = _conditional(lines, pos, ctx, _eval_condition(rest, ctx))
        elif name == 'ifdef':
            pos = _conditional(lines, pos, ctx, _is_defined(_ifdef_identifier(rest), ctx))
        elif name == 'ifndef':
            pos = _conditional(lines, pos, ctx, not _is_defined(_ifdef_identifier(rest), ctx))
        elif name in ('elif', 'else', 'endif'):
            raise ValueError(f'get-content-mrs-preprocessor: unexpected #{name}')
        else:
            pos += 1

    if stops:
        raise ValueError('get-content-mrs-preprocessor: unterminated conditional')
    return pos


def _skip(lines, pos, stops):
    """Advance over (inactive) lines until a ``stops`` directive at depth 0."""
    depth = 0
    while pos < len(lines):
        parsed = _parse_directive(lines[pos])
        name = parsed[0] if parsed else None

        if name is not None and depth == 0 and name in stops:
            return pos, name, parsed[1]
        if name in ('if', 'ifdef', 'ifndef'):
            depth += 1
        elif name == 'endif':
            depth -= 1
        pos += 1
    raise ValueError('get-content-mrs-preprocessor: unterminated conditional')


def _conditional(lines, pos, ctx, initial_condition):
    pos += 1  # skip the opening #if / #ifdef / #ifndef line
    active = bool(initial_condition)
    taken = bool(initial_condition)
    stops = frozenset(('elif', 'else', 'endif'))

    while True:
        if active:
            pos, term, rest = _process(lines, pos, ctx, stops)
        else:
            pos, term, rest = _skip(lines, pos, stops)

        if term == 'endif':
            return pos + 1
        if term == 'elif':
            if not taken:
                active = bool(_eval_condition(rest, ctx))
                taken = active
            else:
                active = False
            pos += 1
        elif term == 'else':
            active = not taken
            taken = True
            pos += 1
        else:
            raise ValueError('get-content-mrs-preprocessor: unterminated conditional')


_IFDEF_IDENT_RE = re.compile(r'^\s*(?:\(\s*)?(' + _IDENTIFIER + r')')


def _ifdef_identifier(rest):
    match = _IFDEF_IDENT_RE.match(rest)
    if not match:
        raise ValueError(f'get-content-mrs-preprocessor: malformed #ifdef/#ifndef {rest!r}')
    return match.group(1)


# ---- substitution -----------------------------------------------------------


def _substitute(text, definitions, case_insensitive):
    """Replace one layer of known identifiers in ``text`` with their bodies."""
    if not definitions:
        return text
    names = sorted(definitions, key=len, reverse=True)
    flags = re.IGNORECASE if case_insensitive else 0
    pattern = re.compile(
        r'(?<![A-Za-z0-9_])(' + '|'.join(re.escape(name) for name in names) + r')(?![A-Za-z0-9_])',
        flags,
    )

    def replace(match):
        return definitions[_canonical(match.group(1), case_insensitive)]

    return pattern.sub(replace, text)


def _substitute_fixpoint(text, definitions, case_insensitive):
    for _ in range(_MAX_PASSES):
        new = _substitute(text, definitions, case_insensitive)
        if new == text:
            return new
        text = new
    raise ValueError(
        'get-content-mrs-preprocessor: recursive macro expansion (no fixpoint)'
    )


def _expand_all(definitions, case_insensitive):
    """Expand every definition to a fixpoint over the whole dictionary."""
    expanded = dict(definitions)
    for _ in range(_MAX_PASSES):
        new = {
            name: _substitute(body, expanded, case_insensitive)
            for name, body in expanded.items()
        }
        if new == expanded:
            return new
        expanded = new
    raise ValueError(
        'get-content-mrs-preprocessor: recursive macro definitions (no fixpoint)'
    )


# ---- #if expression evaluation ----------------------------------------------

_DEFINED_PAREN_RE = re.compile(
    r'\bdefined\s*\(\s*(' + _IDENTIFIER + r')\s*\)', re.IGNORECASE
)
_DEFINED_BARE_RE = re.compile(
    r'\bdefined\s+(' + _IDENTIFIER + r')', re.IGNORECASE
)


def _eval_condition(text, ctx):
    def defined_repl(match):
        return '1' if _is_defined(match.group(1), ctx) else '0'

    text = _DEFINED_PAREN_RE.sub(defined_repl, text)
    text = _DEFINED_BARE_RE.sub(defined_repl, text)
    text = _substitute_fixpoint(text, ctx['definitions'], ctx['case_insensitive'])
    return bool(_eval_numeric_expression(text))


def _tokenize(expr):
    tokens = []
    i = 0
    n = len(expr)
    while i < n:
        ch = expr[i]
        if ch.isspace():
            i += 1
            continue

        if ch.isdigit():
            if ch == '0' and i + 1 < n and expr[i + 1] in 'xXbBoO':
                prefix = expr[i + 1].lower()
                j = i + 2
                if prefix == 'x':
                    digits = '0123456789abcdefABCDEF'
                elif prefix == 'b':
                    digits = '01'
                else:
                    digits = '01234567'
                while j < n and expr[j] in digits:
                    j += 1
                if j == i + 2:
                    raise ValueError(
                        f'get-content-mrs-preprocessor: malformed number '
                        f'{expr[i:j]!r} in #if condition'
                    )
                tokens.append(('num', int(expr[i:j], 0)))
                i = j
            else:
                j = i
                while j < n and expr[j].isdigit():
                    j += 1
                tokens.append(('num', int(expr[i:j], 10)))
                i = j
            continue

        if ch.isalpha() or ch == '_':
            j = i
            while j < n and (expr[j].isalnum() or expr[j] == '_'):
                j += 1
            tokens.append(('ident', expr[i:j]))
            i = j
            continue

        two = expr[i:i + 2]
        if two in ('&&', '||', '==', '!=', '<=', '>='):
            tokens.append(('op', two))
            i += 2
            continue
        if ch in '+-*/%()<>!':
            tokens.append(('op', ch))
            i += 1
            continue

        raise ValueError(
            f'get-content-mrs-preprocessor: unexpected character {ch!r} in #if condition'
        )

    tokens.append(('eof', None))
    return tokens


def _c_div(left, right):
    result = abs(left) // abs(right)
    if (left < 0) != (right < 0):
        result = -result
    return result


def _c_mod(left, right):
    return left - _c_div(left, right) * right


class _ExprParser:
    def __init__(self, tokens):
        self._tokens = tokens
        self._pos = 0

    def _peek(self):
        return self._tokens[self._pos]

    def _advance(self):
        token = self._tokens[self._pos]
        self._pos += 1
        return token

    def parse(self):
        value = self._parse_or()
        kind, text = self._peek()
        if kind != 'eof':
            raise ValueError(
                f'get-content-mrs-preprocessor: unexpected token {text!r} in #if condition'
            )
        return value

    def _parse_or(self):
        value = self._parse_and()
        while self._peek()[1] == '||':
            self._advance()
            value = bool(value) or bool(self._parse_and())
        return value

    def _parse_and(self):
        value = self._parse_eq()
        while self._peek()[1] == '&&':
            self._advance()
            value = bool(value) and bool(self._parse_eq())
        return value

    def _parse_eq(self):
        value = self._parse_rel()
        while self._peek()[1] in ('==', '!='):
            op = self._advance()[1]
            right = self._parse_rel()
            value = value == right if op == '==' else value != right
        return value

    def _parse_rel(self):
        value = self._parse_add()
        while self._peek()[1] in ('<', '<=', '>', '>='):
            op = self._advance()[1]
            right = self._parse_add()
            if op == '<':
                value = value < right
            elif op == '<=':
                value = value <= right
            elif op == '>':
                value = value > right
            else:
                value = value >= right
        return value

    def _parse_add(self):
        value = self._parse_mul()
        while self._peek()[1] in ('+', '-'):
            op = self._advance()[1]
            right = self._parse_mul()
            value = value + right if op == '+' else value - right
        return value

    def _parse_mul(self):
        value = self._parse_unary()
        while self._peek()[1] in ('*', '/', '%'):
            op = self._advance()[1]
            right = self._parse_unary()
            try:
                if op == '*':
                    value = value * right
                elif op == '/':
                    value = _c_div(value, right)
                else:
                    value = _c_mod(value, right)
            except ZeroDivisionError as error:
                raise ValueError(
                    'get-content-mrs-preprocessor: division by zero in #if condition'
                ) from error
        return value

    def _parse_unary(self):
        token = self._peek()
        if token[1] in ('!', '-', '+'):
            self._advance()
            operand = self._parse_unary()
            if token[1] == '!':
                return not operand
            return -operand if token[1] == '-' else operand
        return self._parse_primary()

    def _parse_primary(self):
        kind, text = self._peek()
        if kind == 'num':
            self._advance()
            return text
        if kind == 'ident':
            self._advance()
            return 0  # undefined identifiers evaluate to 0 (C semantics)
        if text == '(':
            self._advance()
            value = self._parse_or()
            if self._peek()[1] != ')':
                raise ValueError(
                    'get-content-mrs-preprocessor: expected ")" in #if condition'
                )
            self._advance()
            return value
        raise ValueError(
            f'get-content-mrs-preprocessor: expected a number or "(" in #if condition, '
            f'got {text!r}'
        )


def _eval_numeric_expression(text):
    return _ExprParser(_tokenize(text)).parse()


import inspect
import operator
from datetime import date, datetime

from .registry import normalize_args
from .sysmissing import is_sysmissing


class ComparisonRegistry:
    """Global registry of comparison ops, keyed by op name.

    A comparison op is a plain function ``(left, right, args=None) -> bool``
    comparing two values. ``args`` is an optional mapping of op-specific options
    (e.g. ``eq`` accepts ``{'unordered_arrays': True}``). Register an op with
    ``@comparisons.register('<name>')``.

    The decorator also records editor metadata: ``op_args`` (a list of arg
    schemas the rule form renders as op-specific inputs) and ``help`` (a short
    description, defaulting to the function docstring).
    """

    def __init__(self):
        self._ops = {}
        self._meta = {}

    def register(self, name, help=None, op_args=None):
        def decorator(fn):
            self._ops[name] = fn
            self._meta[name] = {
                'name': name,
                'help': help if help is not None else (inspect.getdoc(fn) or ''),
                'op_args': normalize_args(op_args),
            }
            return fn
        return decorator

    def get(self, name):
        if name not in self._ops:
            raise KeyError(f'comparison op not found: {name}')
        return self._ops[name]

    def names(self):
        return list(self._ops)

    def describe(self, name):
        return self._meta.get(name)

    def metadata(self):
        return [self._meta[name] for name in self._ops]


comparisons = ComparisonRegistry()


def _is_bool(value):
    return isinstance(value, bool)


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_text(value):
    return isinstance(value, str)


def _is_datetime_like(value):
    return isinstance(value, (date, datetime))


def _is_block(value):
    return isinstance(value, dict)


def _is_array(value):
    return isinstance(value, list)


def _arrays_equal_unordered(left, right, args):
    """Order-agnostic (multiset) array equality under recursive ``eq``."""
    if len(left) != len(right):
        return False
    remaining = list(right)
    for item in left:
        for i, candidate in enumerate(remaining):
            if eq(item, candidate, args):
                remaining.pop(i)
                break
        else:
            return False
    return True


def _to_number(value):
    """Return the numeric value of ``value`` if it is a number or a numeric
    string (e.g. ``"42"``, ``"3.14"``), otherwise ``None``.

    Booleans and non-numeric text are deliberately excluded (``True`` and
    ``"abc"`` are not numbers).
    """
    if _is_number(value):
        return value
    if _is_text(value):
        text = value.strip()
        if text == '':
            return None
        try:
            return int(text)
        except ValueError:
            try:
                return float(text)
            except ValueError:
                return None
    return None


@comparisons.register(
    'eq',
    help='Equal (deep; arrays order-sensitive unless unordered_arrays).',
    op_args=[
        {
            'name': 'unordered_arrays',
            'type': 'boolean',
            'required': False,
            'default': False,
            'description': 'Compare arrays as multisets (order does not matter).',
        },
    ],
)
def eq(left, right, args=None):
    unordered = bool(args and args.get('unordered_arrays'))
    if is_sysmissing(left) or is_sysmissing(right):
        return is_sysmissing(left) and is_sysmissing(right)
    if _is_block(left) or _is_block(right):
        return (
            _is_block(left) and _is_block(right)
            and left.keys() == right.keys()
            and all(eq(left[key], right[key], args) for key in left)
        )
    if _is_array(left) or _is_array(right):
        if not (_is_array(left) and _is_array(right)):
            return False
        if unordered:
            return _arrays_equal_unordered(left, right, args)
        return (
            len(left) == len(right)
            and all(eq(a, b, args) for a, b in zip(left, right))
        )
    if _is_bool(left) or _is_bool(right):
        return _is_bool(left) and _is_bool(right) and left == right
    left_num = _to_number(left)
    right_num = _to_number(right)
    if left_num is not None and right_num is not None:
        return left_num == right_num
    if left_num is not None or right_num is not None:
        return False
    return left == right


@comparisons.register(
    'ne',
    help='Not equal.',
    op_args=[
        {
            'name': 'unordered_arrays',
            'type': 'boolean',
            'required': False,
            'default': False,
            'description': 'Compare arrays as multisets (order does not matter).',
        },
    ],
)
def ne(left, right, args=None):
    return not eq(left, right, args)


@comparisons.register('eq-unordered', help='Equal with order-agnostic arrays.')
def eq_unordered(left, right, args=None):
    return eq(left, right, {'unordered_arrays': True})


def _ordered(op, left, right):
    if is_sysmissing(left) or is_sysmissing(right):
        return False
    if _is_bool(left) or _is_bool(right):
        return False
    left_num = _to_number(left)
    right_num = _to_number(right)
    if left_num is not None and right_num is not None:
        return op(left_num, right_num)
    if left_num is not None or right_num is not None:
        return False
    left_dt = _is_datetime_like(left)
    right_dt = _is_datetime_like(right)
    if left_dt or right_dt:
        return op(left, right) if (left_dt and right_dt) else False
    if _is_text(left) and _is_text(right):
        return op(left, right)
    return False


@comparisons.register('lt', help='Less than (scalar only).')
def lt(left, right, args=None):
    return _ordered(operator.lt, left, right)


@comparisons.register('le', help='Less than or equal (scalar only).')
def le(left, right, args=None):
    return _ordered(operator.le, left, right)


@comparisons.register('gt', help='Greater than (scalar only).')
def gt(left, right, args=None):
    return _ordered(operator.gt, left, right)


@comparisons.register('ge', help='Greater than or equal (scalar only).')
def ge(left, right, args=None):
    return _ordered(operator.ge, left, right)


@comparisons.register(
    'contains',
    help='Membership (substring for text, membership for arrays).',
)
def contains(left, right, args=None):
    if is_sysmissing(left) or is_sysmissing(right):
        return False
    try:
        return right in left
    except TypeError:
        return False

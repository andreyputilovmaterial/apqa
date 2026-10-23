
import operator
from datetime import date, datetime

from .sysmissing import is_sysmissing


class ComparisonRegistry:
    """Global registry of comparison ops, keyed by op name.

    A comparison op is a plain function ``(left, right) -> bool`` comparing two
    scalars. Register an op with ``@comparisons.register('<name>')``.
    """

    def __init__(self):
        self._ops = {}

    def register(self, name):
        def decorator(fn):
            self._ops[name] = fn
            return fn
        return decorator

    def get(self, name):
        if name not in self._ops:
            raise KeyError(f'comparison op not found: {name}')
        return self._ops[name]

    def names(self):
        return list(self._ops)


comparisons = ComparisonRegistry()


def _is_bool(value):
    return isinstance(value, bool)


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_text(value):
    return isinstance(value, str)


def _is_datetime_like(value):
    return isinstance(value, (date, datetime))


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


@comparisons.register('eq')
def eq(left, right):
    if is_sysmissing(left) or is_sysmissing(right):
        return is_sysmissing(left) and is_sysmissing(right)
    if _is_bool(left) or _is_bool(right):
        return _is_bool(left) and _is_bool(right) and left == right
    left_num = _to_number(left)
    right_num = _to_number(right)
    if left_num is not None and right_num is not None:
        return left_num == right_num
    if left_num is not None or right_num is not None:
        return False
    return left == right


@comparisons.register('ne')
def ne(left, right):
    return not eq(left, right)


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


@comparisons.register('lt')
def lt(left, right):
    return _ordered(operator.lt, left, right)


@comparisons.register('le')
def le(left, right):
    return _ordered(operator.le, left, right)


@comparisons.register('gt')
def gt(left, right):
    return _ordered(operator.gt, left, right)


@comparisons.register('ge')
def ge(left, right):
    return _ordered(operator.ge, left, right)


@comparisons.register('contains')
def contains(left, right):
    if is_sysmissing(left) or is_sysmissing(right):
        return False
    try:
        return right in left
    except TypeError:
        return False

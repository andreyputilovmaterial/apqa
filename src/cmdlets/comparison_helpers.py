"""Shared helpers for the ``cmp-*`` comparison ops."""

from datetime import date, datetime

from .sysmissing import is_sysmissing


def is_bool(value):
    return isinstance(value, bool)


def is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def is_text(value):
    return isinstance(value, str)


def is_datetime_like(value):
    return isinstance(value, (date, datetime))


def is_block(value):
    return isinstance(value, dict)


def is_array(value):
    return isinstance(value, list)


def to_number(value):
    """Return the numeric value of ``value`` if it is a number or a numeric
    string (e.g. ``"42"``, ``"3.14"``), otherwise ``None``.

    Booleans and non-numeric text are deliberately excluded (``True`` and
    ``"abc"`` are not numbers).
    """
    if is_number(value):
        return value
    if is_text(value):
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


def ordered_compare(op, left, right):
    """Scalar-only ordering comparison (``<`` / ``<=`` / ``>`` / ``>=``).

    ``sysmissing`` and booleans are never orderable (they return ``False``);
    numbers unify, numeric strings coerce to numbers, text compares
    lexicographically and date/times compare chronologically (both
    timezone-aware).
    """
    if is_sysmissing(left) or is_sysmissing(right):
        return False
    if is_bool(left) or is_bool(right):
        return False
    left_num = to_number(left)
    right_num = to_number(right)
    if left_num is not None and right_num is not None:
        return op(left_num, right_num)
    if left_num is not None or right_num is not None:
        return False
    left_dt = is_datetime_like(left)
    right_dt = is_datetime_like(right)
    if left_dt or right_dt:
        return op(left, right) if (left_dt and right_dt) else False
    if is_text(left) and is_text(right):
        return op(left, right)
    return False

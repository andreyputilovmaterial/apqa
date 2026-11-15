"""SQL three-valued (Kleene) logic helpers for the ``logical-tristate-*`` cmdlets.

The three truth values are ``True`` (true), ``False`` (false), and ``None``
(unknown — the ``sysmissing`` value). Non-boolean operands are coerced with
``bool()`` exactly like the plain ``logical-*`` cmdlets; only ``sysmissing``
(``None``) is treated as unknown instead of false.
"""

from .sysmissing import is_sysmissing


def as_tristate(value):
    """Map a value to a three-valued boolean: ``True``, ``False``, or ``None``."""
    if is_sysmissing(value):
        return None
    return bool(value)


def tristate_not(value):
    """``NOT`` (SQL semantics): unknown negates to unknown."""
    truth = as_tristate(value)
    if truth is None:
        return None
    return not truth


def tristate_and(values):
    """``AND`` over ``values`` (SQL semantics): false dominates, then unknown."""
    has_unknown = False
    for value in values:
        truth = as_tristate(value)
        if truth is False:
            return False
        if truth is None:
            has_unknown = True
    return None if has_unknown else True


def tristate_or(values):
    """``OR`` over ``values`` (SQL semantics): true dominates, then unknown."""
    has_unknown = False
    for value in values:
        truth = as_tristate(value)
        if truth is True:
            return True
        if truth is None:
            has_unknown = True
    return None if has_unknown else False

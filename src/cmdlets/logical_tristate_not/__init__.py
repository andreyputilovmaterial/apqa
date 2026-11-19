"""`logical-tristate-not` — SQL-style three-valued negation."""

from ..registry import cmdlets
from ..tristate import tristate_not
from ..value_types import Boolean, PipeValue, coerce, sysmissing


@cmdlets.register('logical-tristate-not', kind='processor')
def logical_tristate_not(value: PipeValue, args: dict) -> PipeValue:
    """Return the SQL-style negation of ``value``.

    ``True`` negates to ``False``, ``False`` negates to ``True``, and
    ``sysmissing`` (unknown) negates to ``sysmissing``. Other values are coerced
    with ``bool()`` first.
    """
    result = tristate_not(coerce(value))
    return sysmissing if result is None else Boolean(result)


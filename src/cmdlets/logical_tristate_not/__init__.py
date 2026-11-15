"""`logical-tristate-not` — SQL-style three-valued negation."""

from typing import Optional

from ..registry import cmdlets
from ..tristate import tristate_not
from ..value_types import Boolean, PipeValue


@cmdlets.register('logical-tristate-not', kind='processor')
def logical_tristate_not(value: PipeValue, args: dict) -> Optional[Boolean]:
    """Return the SQL-style negation of ``value``.

    ``True`` negates to ``False``, ``False`` negates to ``True``, and
    ``sysmissing`` (unknown) negates to ``sysmissing``. Other values are coerced
    with ``bool()`` first, so ``not sysmissing`` resolves to ``sysmissing``.
    """
    return tristate_not(value)

"""`logical-tristate-any` — SQL-style three-valued OR over an array."""

from typing import Optional

from ..registry import cmdlets
from ..tristate import tristate_or
from ..value_types import Boolean, PipeValue


@cmdlets.register('logical-tristate-any', kind='processor')
def logical_tristate_any(value: PipeValue, args: dict) -> Optional[Boolean]:
    """Return the SQL-style three-valued OR over an array's iterations.

    ``True`` if any iteration is truthy; ``sysmissing`` if no iteration is
    truthy but at least one is ``sysmissing`` (unknown); ``False`` only when
    every iteration is falsy. An empty array is ``False``.
    """
    if not isinstance(value, list):
        raise TypeError(
            f'logical-tristate-any: expected an array, got {type(value).__name__}'
        )
    return tristate_or(value)

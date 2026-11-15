"""`logical-tristate-all` — SQL-style three-valued AND over an array."""

from typing import Optional

from ..registry import cmdlets
from ..tristate import tristate_and
from ..value_types import Boolean, PipeValue


@cmdlets.register('logical-tristate-all', kind='processor')
def logical_tristate_all(value: PipeValue, args: dict) -> Optional[Boolean]:
    """Return the SQL-style three-valued AND over an array's iterations.

    ``False`` if any iteration is falsy; ``sysmissing`` if no iteration is falsy
    but at least one is ``sysmissing`` (unknown); ``True`` only when every
    iteration is truthy. An empty array is ``True``.
    """
    if not isinstance(value, list):
        raise TypeError(
            f'logical-tristate-all: expected an array, got {type(value).__name__}'
        )
    return tristate_and(value)

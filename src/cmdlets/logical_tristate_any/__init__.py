"""`logical-tristate-any` — SQL-style three-valued OR over the piped value."""

from typing import Optional

from ..registry import cmdlets
from ..tree import iter_leaves
from ..tristate import tristate_or
from ..value_types import Boolean, PipeValue


@cmdlets.register('logical-tristate-any', kind='processor')
def logical_tristate_any(value: PipeValue, args: dict) -> Optional[Boolean]:
    """Return the SQL-style three-valued OR over the value's scalar leaves.

    ``True`` if any leaf is truthy; ``sysmissing`` if no leaf is truthy but at
    least one is ``sysmissing`` (unknown); ``False`` only when every leaf is
    falsy. An empty block/array is ``False``. A scalar value is a single leaf.
    """
    return tristate_or(iter_leaves(value))

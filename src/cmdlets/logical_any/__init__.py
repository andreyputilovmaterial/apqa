"""`logical-any` — any scalar leaf of the piped value is truthy."""

from ..registry import cmdlets
from ..tree import iter_leaves
from ..value_types import Boolean, PipeValue


@cmdlets.register('logical-any', kind='processor')
def logical_any(value: PipeValue, args: dict) -> Boolean:
    """Return ``True`` iff any scalar leaf of the value is truthy.

    Blocks and arrays are traversed recursively; a scalar value is treated as a
    single leaf. An empty block/array is ``False``.
    """
    return any(bool(item) for item in iter_leaves(value))

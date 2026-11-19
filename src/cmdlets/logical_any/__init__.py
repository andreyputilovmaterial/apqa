"""`logical-any` — any scalar leaf of the piped value is truthy."""

from ..registry import cmdlets
from ..value_types import Boolean, PipeValue, coerce


@cmdlets.register('logical-any', kind='processor')
def logical_any(value: PipeValue, args: dict) -> Boolean:
    """Return ``True`` iff any scalar leaf of the value is truthy.

    Blocks and collections are traversed recursively; a scalar value is treated
    as a single leaf. An empty block/collection is ``False``.
    """
    return Boolean(any(bool(item) for item in coerce(value).iter_leaves()))


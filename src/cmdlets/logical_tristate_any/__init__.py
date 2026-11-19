"""`logical-tristate-any` — SQL-style three-valued OR over the piped value."""

from ..registry import cmdlets
from ..tristate import tristate_or
from ..value_types import Boolean, PipeValue, coerce, sysmissing


@cmdlets.register('logical-tristate-any', kind='processor')
def logical_tristate_any(value: PipeValue, args: dict) -> PipeValue:
    """Return the SQL-style three-valued OR over the value's scalar leaves.

    ``True`` if any leaf is truthy; ``sysmissing`` if no leaf is truthy but at
    least one is ``sysmissing`` (unknown); ``False`` only when every leaf is
    falsy. An empty block/collection is ``False``. A scalar value is a single leaf.
    """
    result = tristate_or(coerce(value).iter_leaves())
    return sysmissing if result is None else Boolean(result)


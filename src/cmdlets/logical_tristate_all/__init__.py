"""`logical-tristate-all` — SQL-style three-valued AND over the piped value."""

from ..registry import cmdlets
from ..tristate import tristate_and
from ..value_types import Boolean, PipeValue, coerce, sysmissing


@cmdlets.register('logical-tristate-all', kind='processor')
def logical_tristate_all(value: PipeValue, args: dict) -> PipeValue:
    """Return the SQL-style three-valued AND over the value's scalar leaves.

    ``False`` if any leaf is falsy; ``sysmissing`` if no leaf is falsy but at
    least one is ``sysmissing`` (unknown); ``True`` only when every leaf is
    truthy. An empty block/collection is ``True``. A scalar value is a single leaf.
    """
    result = tristate_and(coerce(value).iter_leaves())
    return sysmissing if result is None else Boolean(result)


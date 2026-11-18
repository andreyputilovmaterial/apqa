"""`logical-tristate-all` — SQL-style three-valued AND over the piped value."""

from typing import Optional

from ..registry import cmdlets
from ..tree import iter_leaves
from ..tristate import tristate_and
from ..value_types import Boolean, PipeValue


@cmdlets.register('logical-tristate-all', kind='processor')
def logical_tristate_all(value: PipeValue, args: dict) -> Optional[Boolean]:
    """Return the SQL-style three-valued AND over the value's scalar leaves.

    ``False`` if any leaf is falsy; ``sysmissing`` if no leaf is falsy but at
    least one is ``sysmissing`` (unknown); ``True`` only when every leaf is
    truthy. An empty block/array is ``True``. A scalar value is a single leaf.
    """
    return tristate_and(iter_leaves(value))

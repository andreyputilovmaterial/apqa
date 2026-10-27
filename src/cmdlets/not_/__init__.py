"""`not` — logical negation of the incoming value's boolean."""

from ..registry import cmdlets
from ..value_types import Boolean, PipeValue


@cmdlets.register('not', kind='processor')
def not_(value: PipeValue, args: dict) -> Boolean:
    """Return the boolean negation of ``value`` (``not`` of its truthiness).

    ``not sysmissing`` is ``True``.
    """
    return not bool(value)

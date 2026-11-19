"""`logical-not` — logical negation of the incoming value's boolean."""

from ..registry import cmdlets
from ..value_types import Boolean, PipeValue, coerce


@cmdlets.register('logical-not', kind='processor')
def logical_not(value: PipeValue, args: dict) -> Boolean:
    """Return the boolean negation of ``value`` (``not`` of its truthiness).

    ``not sysmissing`` is ``True``.
    """
    return Boolean(not bool(coerce(value)))


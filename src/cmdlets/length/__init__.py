"""`length` — the length of text."""

from ..registry import cmdlets
from ..value_types import Integer, PipeValue, coerce


@cmdlets.register('length', kind='processor')
def length(value: PipeValue, args: dict) -> Integer:
    """Return the number of characters in the text value."""
    return Integer(coerce(value).length())


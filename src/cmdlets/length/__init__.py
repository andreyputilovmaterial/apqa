"""`length` — the length of text."""

from ..registry import cmdlets
from ..value_types import Integer, PipeValue


@cmdlets.register('length', kind='processor')
def length(value: PipeValue, args: dict) -> Integer:
    """Return the number of characters in the text value."""
    if not isinstance(value, str):
        raise TypeError(f'length: expected text, got {type(value).__name__}')
    return len(value)

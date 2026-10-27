"""`as-integer` — convert a value to an integer."""

from ..registry import cmdlets
from ..value_types import Integer, PipeValue


@cmdlets.register('as-integer', kind='processor')
def as_integer(value: PipeValue, args: dict) -> Integer:
    """Convert ``value`` to an integer via Python's ``int()``.

    Native conversion errors propagate (e.g. ``int('3.14')`` or ``int(None)``).
    """
    return int(value)

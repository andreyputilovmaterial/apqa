"""`bit-not` — bitwise NOT of an integer."""

from ..operands import require_int
from ..registry import cmdlets
from ..value_types import Integer, PipeValue


@cmdlets.register('bit-not')
def bit_not(value: PipeValue, args: dict) -> Integer:
    """Return ``~value``; the value must be an integer (bool excluded)."""
    return ~require_int(value, 'bit-not')

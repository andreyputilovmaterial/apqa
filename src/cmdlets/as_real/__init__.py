"""`as-real` — convert a value to a floating-point number."""

from ..registry import cmdlets
from ..value_types import PipeValue, Real


@cmdlets.register('as-real', kind='processor')
def as_real(value: PipeValue, args: dict) -> Real:
    """Convert ``value`` to a real via Python's ``float()``; errors propagate."""
    return float(value)

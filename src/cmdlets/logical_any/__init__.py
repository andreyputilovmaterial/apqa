"""`logical-any` — any iteration of an array is truthy."""

from ..registry import cmdlets
from ..value_types import Boolean, PipeValue


@cmdlets.register('logical-any', kind='processor')
def logical_any(value: PipeValue, args: dict) -> Boolean:
    """Return ``True`` iff any iteration of the array is truthy."""
    if not isinstance(value, list):
        raise TypeError(f'logical-any: expected an array, got {type(value).__name__}')
    return any(bool(item) for item in value)

"""`logical-all` — every iteration of an array is truthy."""

from ..registry import cmdlets
from ..value_types import Boolean, PipeValue


@cmdlets.register('logical-all', kind='processor')
def logical_all(value: PipeValue, args: dict) -> Boolean:
    """Return ``True`` iff every iteration of the array is truthy."""
    if not isinstance(value, list):
        raise TypeError(f'logical-all: expected an array, got {type(value).__name__}')
    return all(bool(item) for item in value)

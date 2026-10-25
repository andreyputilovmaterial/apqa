"""`as-boolean` — convert a value to boolean."""

from ..registry import cmdlets
from ..value_types import Boolean, PipeValue


@cmdlets.register('as-boolean')
def as_boolean(value: PipeValue, args: dict) -> Boolean:
    """Convert ``value`` to a boolean using Python's truthiness.

    ``sysmissing``, an empty string, an empty array/block, and zero become
    ``False``; any other stored value becomes ``True``. This matches ``count``,
    which returns 0 for those same empty cases.
    """
    return bool(value)

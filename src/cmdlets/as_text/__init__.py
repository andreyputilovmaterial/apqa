"""`as-text` — convert a value to text."""

from ..registry import cmdlets
from ..sysmissing import is_sysmissing
from ..value_types import PipeValue, Text


@cmdlets.register('as-text')
def as_text(value: PipeValue, args: dict) -> Text:
    """Convert ``value`` to text using Python's natural ``str()``.

    ``sysmissing`` (``None``) becomes the empty string, never ``"None"``.
    """
    return '' if is_sysmissing(value) else str(value)

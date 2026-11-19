"""`as-text` — convert a value to text."""

from ..registry import cmdlets
from ..value_types import PipeValue, Text, coerce


@cmdlets.register('as-text', kind='processor')
def as_text(value: PipeValue, args: dict) -> Text:
    """Convert ``value`` to text using the value's natural text rendering.

    ``sysmissing`` becomes the empty string, never ``"None"``.
    """
    return Text(coerce(value).as_text())


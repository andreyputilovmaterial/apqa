"""`get-content` — proxy for `get-content-text`.

Reads a text file into a single text value. This is the familiar ``get-content``
name kept as a proxy/alias for ``get-content-text``; it delegates to that cmdlet
and shares its arguments, so the two names are interchangeable.
"""

from ..registry import cmdlets
from ..value_types import PipeValue, Text
from ..get_content_text import ARGS, get_content_text


@cmdlets.register(
    'get-content',
    kind='source',
    help='Proxy for get-content-text: read a text file into a single text value.',
    args=ARGS,
)
def get_content(value: PipeValue, args: dict) -> Text:
    return get_content_text(value, args)

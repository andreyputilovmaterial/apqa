"""`transform-text-count-chars` — the number of characters in text.

Processor cmdlet: it takes a text value and returns its length as an integer.
With ``args['strip_whitespace']`` (bool, default ``false``), leading and
trailing whitespace is removed first (Python's ``str.strip``).

A non-text value (including ``sysmissing``) raises, mirroring the other
``transform-text-*`` cmdlets.
"""

from ..registry import cmdlets
from ..value_types import Integer, PipeValue, Text, coerce


@cmdlets.register(
    'transform-text-count-chars',
    kind='processor',
    args=[
        {
            'name': 'strip_whitespace',
            'type': 'boolean',
            'required': False,
            'default': False,
            'description': 'Strip leading and trailing whitespace before counting.',
        },
    ],
)
def transform_text_count_chars(value: PipeValue, args: dict) -> Integer:
    """Return the number of characters in the text value."""
    value = coerce(value)
    if not isinstance(value, Text):
        raise TypeError(
            f'transform-text-count-chars: expected text, got {value.type_name}'
        )

    text = value.value
    if bool(args.get('strip_whitespace', False)):
        text = text.strip()
    return Integer(len(text))


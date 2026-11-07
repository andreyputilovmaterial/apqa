"""`transform-text-regex` — replace regex matches in text with a replacement.

Processor cmdlet: it takes a text value and returns text. Every match of
``args['pattern']`` (a regular expression) is replaced with
``args['replacement']`` using Python's ``re.sub``, so replacement backreferences
such as ``\\1`` are supported.

Args (stored named mapping):

    pattern           regular expression to search for (required).
    replacement       replacement text (required; an empty string deletes every
                      match; backreferences like ``\\1`` are supported).
    case_insensitive  bool, default ``false`` — match case-insensitively.
    count             number, default ``0`` — maximum number of replacements
                      (``0`` replaces every match).

A non-text value (including ``sysmissing``) raises, mirroring the ``matches``
and ``length`` string helpers.
"""

import re

from ..registry import cmdlets
from ..value_types import PipeValue, Text


@cmdlets.register(
    'transform-text-regex',
    kind='processor',
    args=[
        {
            'name': 'pattern',
            'type': 'text',
            'required': True,
            'description': 'Regular expression to search for.',
        },
        {
            'name': 'replacement',
            'type': 'text',
            'required': True,
            'description': 'Replacement text (backreferences like \\1 are supported).',
        },
        {
            'name': 'case_insensitive',
            'type': 'boolean',
            'required': False,
            'default': False,
            'description': 'Ignore case when matching.',
        },
        {
            'name': 'count',
            'type': 'number',
            'required': False,
            'default': 0,
            'description': 'Maximum number of replacements (0 replaces all).',
        },
    ],
)
def transform_text_regex(value: PipeValue, args: dict) -> Text:
    """Replace regex matches of ``args['pattern']`` with ``args['replacement']``."""
    if not isinstance(value, str):
        raise TypeError(f'transform-text-regex: expected text, got {type(value).__name__}')

    pattern = args.get('pattern')
    if pattern is None or str(pattern) == '':
        raise ValueError("transform-text-regex: missing required arg 'pattern'")
    replacement = args.get('replacement')
    if replacement is None:
        raise ValueError("transform-text-regex: missing required arg 'replacement'")

    pattern = str(pattern)
    replacement = str(replacement)
    flags = re.IGNORECASE if bool(args.get('case_insensitive', False)) else 0
    count = _coerce_count(args.get('count', 0))

    return re.sub(pattern, replacement, value, count=count, flags=flags)


def _coerce_count(value):
    if value is None:
        return 0
    if isinstance(value, bool):
        raise ValueError(
            "transform-text-regex: 'count' must be a non-negative integer, got a boolean"
        )
    try:
        count = int(value)
    except (TypeError, ValueError):
        raise ValueError(
            "transform-text-regex: 'count' must be a non-negative integer, got "
            f'{value!r}'
        ) from None
    if count < 0:
        raise ValueError(
            "transform-text-regex: 'count' must be a non-negative integer, got "
            f'{value!r}'
        )
    return count

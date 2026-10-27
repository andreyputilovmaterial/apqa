"""`matches` — does the text contain/match a pattern?"""

import re

from ..registry import cmdlets
from ..value_types import Boolean, PipeValue


@cmdlets.register(
    'matches',
    kind='processor',
    args=[
        {'name': 'pattern', 'type': 'text', 'required': True, 'description': 'Substring or regular expression to look for.'},
        {
            'name': 'case_insensitive',
            'type': 'boolean',
            'required': False,
            'default': False,
            'description': 'Ignore case when matching.',
        },
        {
            'name': 'regex',
            'type': 'boolean',
            'required': False,
            'default': False,
            'description': 'Treat the pattern as a regular expression.',
        },
    ],
)
def matches(value: PipeValue, args: dict) -> Boolean:
    """Return ``True`` when the text matches ``args['pattern']``.

    By default a case-sensitive literal substring search.
    ``args['case_insensitive']`` ignores case; ``args['regex']`` treats the
    pattern as a regular expression (``re.search``).
    """
    if not isinstance(value, str):
        raise TypeError(f'matches: expected text, got {type(value).__name__}')
    pattern = args.get('pattern')
    if pattern is None or pattern == '':
        raise ValueError("matches: missing required arg 'pattern'")
    pattern = str(pattern)

    case_insensitive = bool(args.get('case_insensitive', False))
    regex = bool(args.get('regex', False))

    if regex:
        flags = re.IGNORECASE if case_insensitive else 0
        return re.search(pattern, value, flags) is not None
    if case_insensitive:
        return pattern.lower() in value.lower()
    return pattern in value

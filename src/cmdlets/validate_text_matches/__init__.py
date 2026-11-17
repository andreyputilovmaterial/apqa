"""`validate-text-matches` — check whether the incoming value's text matches a pattern.

Terminal cmdlet: it answers a yes/no question about the piped value. Only ``text``
values are actually matched — each text leaf is searched for ``args['pattern']``
(a case-sensitive literal substring by default, or a regular expression when
``args['regex']`` is set). Every other scalar (``sysmissing``, booleans, numbers,
dates, paths, …) has no text to match, so it simply passes. Compound values
(blocks and arrays) run the same check on every field/item and combine the
results with a logical ``AND`` (an empty compound value is vacuously valid).

When a text value fails, the cmdlet records a **diagnostic note** (if a run is
collecting notes) whose path points at the offending leaf — e.g.
``['Fields', 'BrandAwareness', 'Label']`` — so the runner can tell the user
exactly which field of which section did not match (see
``docs/qc-results-reporting.md``). The cmdlet still returns a plain ``bool``, so a
rule that compares it to ``literal(True)`` keeps working unchanged.
"""

import re

from ..diagnostic import current_notes
from ..registry import cmdlets
from ..value_types import Boolean, PipeValue


@cmdlets.register(
    'validate-text-matches',
    kind='terminal',
    args=[
        {
            'name': 'pattern',
            'type': 'text',
            'required': True,
            'description': 'Substring or regular expression to look for.',
        },
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
def validate_text_matches(value: PipeValue, args: dict) -> Boolean:
    """Return ``True`` when every text leaf matches ``args['pattern']``.

    By default a case-sensitive literal substring search.
    ``args['case_insensitive']`` ignores case; ``args['regex']`` treats the
    pattern as a regular expression (``re.search``).
    """
    pattern = args.get('pattern')
    if pattern is None or str(pattern) == '':
        raise ValueError("validate-text-matches: missing required arg 'pattern'")
    pattern = str(pattern)

    case_insensitive = bool(args.get('case_insensitive', False))
    regex = bool(args.get('regex', False))

    return _check(value, [], current_notes(), pattern, case_insensitive, regex)


def _check(value, path, notes, pattern, case_insensitive, regex):
    """Recursively validate ``value`` and record a note per failing text leaf."""
    if isinstance(value, str):
        if _matches(value, pattern, case_insensitive, regex):
            return True
        if notes is not None:
            notes.note(
                path,
                f'text does not match {pattern!r} (value: {_clip(value)!r})',
            )
        return False
    if isinstance(value, dict):
        return all(
            _check(field_value, path + [key], notes, pattern, case_insensitive, regex)
            for key, field_value in value.items()
        )
    if isinstance(value, list):
        return all(
            _check(item, path + [index], notes, pattern, case_insensitive, regex)
            for index, item in enumerate(value)
        )
    return True


def _matches(text, pattern, case_insensitive, regex):
    if regex:
        flags = re.IGNORECASE if case_insensitive else 0
        return re.search(pattern, text, flags) is not None
    if case_insensitive:
        return pattern.lower() in text.lower()
    return pattern in text


def _clip(value, limit=80):
    text = f'{value}'
    if len(text) <= limit:
        return text
    return text[:limit - 3] + '...'

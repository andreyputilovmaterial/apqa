"""`transform-text-code-grab-assignments-mrs` — grab assignment values from text.

Processor cmdlet: it takes a text value (e.g. the content of an MRS/script
source file) and returns a **collection of text values** — one element per line
that assigns ``args['variable_name']`` in Basic-style ``NAME = VALUE`` syntax,
where a ``'`` (single quote) starts an inline comment.

The matching is a line-oriented regular expression, applied to the whole text
with Python's ``re.MULTILINE`` so ``^`` anchors to each line start and ``$`` to
each line end:

    ^\\s*<variable_name>\\s*=\\s*([^\\n]*?)\\s*(?:'[^\\n]*?)?\\s*?$

``<variable_name>`` is matched literally (regex-escaped), not as a pattern. The
first capture group — the assigned value up to the trailing whitespace/comment —
is added to the returned collection verbatim, so ``4343`` stays ``4343`` and a
quoted value stays ``"aaa"``. Lines that do not match contribute nothing; an
empty result is an empty collection.

Args (stored named mapping):

    variable_name    text, required — the variable name whose assignment values
                     are grabbed.

A non-text value (including ``sysmissing``) raises, mirroring the
``transform-text-regex`` string helper.
"""

import re

from ..registry import cmdlets
from ..value_types import Collection, PipeValue, Text, coerce


@cmdlets.register(
    'transform-text-code-grab-assignments-mrs',
    kind='processor',
    args=[
        {
            'name': 'variable_name',
            'type': 'text',
            'required': True,
            'description': 'Variable name whose assignment values to grab.',
        },
    ],
)
def transform_text_code_grab_assignments_mrs(value: PipeValue, args: dict) -> Collection:
    """Return a collection of the assigned values of ``args['variable_name']``."""
    value = coerce(value)
    if not isinstance(value, Text):
        raise TypeError(
            f'transform-text-code-grab-assignments-mrs: expected text, got {value.type_name}'
        )

    variable_name = args.get('variable_name')
    if variable_name is None or str(variable_name) == '':
        raise ValueError(
            "transform-text-code-grab-assignments-mrs: missing required arg 'variable_name'"
        )

    pattern = re.compile(
        r'^\s*' + re.escape(str(variable_name)) + r"\s*=\s*([^\n]*?)\s*(?:'[^\n]*?)?\s*?$",
        re.MULTILINE,
    )

    return Collection([match.group(1) for match in pattern.finditer(value.value)])

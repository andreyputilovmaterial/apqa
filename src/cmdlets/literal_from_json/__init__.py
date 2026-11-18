"""`literal-from-json` — parse an exact JSON string into an internal value.

Source reader: the piped value is ignored and the constant is read from
``args['value']`` (the exact JSON text).

This is the `literal` cmdlet's sibling for the case where the constant is
handed over as a JSON *string* (e.g. pasted from another tool) rather than
typed through the literal editor. ``args['value']`` is parsed with
``json.loads``, which maps JSON onto the internal runtime representation
one-to-one: ``null`` -> ``sysmissing`` (``None``), string -> text, number ->
``int``/``float``, boolean -> ``bool``, array -> ``Collection`` (with 1-based
provisional names), object -> ``dict``.
"""

import json

from ..registry import cmdlets
from ..value_types import from_plain, PipeValue


@cmdlets.register(
    'literal-from-json',
    kind='source',
    args=[
        {
            'name': 'value',
            'type': 'text',
            'required': True,
            'description': (
                'The exact JSON text to parse — a string, number, boolean, '
                'null, array, or object.'
            ),
        },
    ],
    compact=[{'arg': 'value'}],
    full=[{'arg': 'value'}],
)
def literal_from_json(value: PipeValue, args: dict) -> PipeValue:
    """Return the value parsed from ``args['value']`` (an exact JSON string).

    ``json.loads`` maps JSON onto the internal runtime representation one-to-one
    (see the module docstring), so ``{"a": 1}`` becomes a block, ``[1, 2]`` a
    collection, and ``null`` -> ``sysmissing``. The incoming ``value`` is ignored.
    """
    raw = args.get('value')
    if raw is None:
        raise ValueError("literal-from-json: missing required arg 'value'")
    try:
        return from_plain(json.loads(raw))
    except json.JSONDecodeError as error:
        raise ValueError(f'literal-from-json: invalid JSON: {error}') from error

"""`select-field` — read one field from a block, or a collection of that field
from every element of a collection.

This is the unified "dot + field" access of the JSON mental model: an object is
a block (read one named field), and a collection is a sequence of blocks (map the
field over every element, like JS ``items.map(x => x.field)``). Nesting is by
chaining — ``select-field "a" | select-field "b"`` is ``obj.a.b``.

With ``missing_ok: true``, a missing field returns ``sysmissing`` instead of
raising — the JS ``obj.missing === undefined`` behaviour. On a collection, each
element that lacks the field contributes ``sysmissing`` at that position.
"""

from ..registry import cmdlets
from ..value_types import PipeValue, coerce


@cmdlets.register(
    'select-field',
    kind='processor',
    help='Read one field from a block, or a flat list of that field from an array.',
    args=[
        {
            'name': 'field',
            'type': 'text',
            'required': True,
            'description': 'The block field (column) name to read.',
        },
        {
            'name': 'missing_ok',
            'type': 'boolean',
            'required': False,
            'default': False,
            'description': 'Return sysmissing instead of failing when the field is missing.',
        },
    ],
    compact=[{'text': '->', 'role': 'arrow'}, {'arg': 'field'}],
)
def select_field(value: PipeValue, args: dict) -> PipeValue:
    """Return ``block[field]`` for a block, or a collection of that field per element."""
    field = args.get('field')
    if field is None:
        raise ValueError("select-field: missing required arg 'field'")

    missing_ok = args.get('missing_ok', False)
    return coerce(value).select_field(field, missing_ok=missing_ok)


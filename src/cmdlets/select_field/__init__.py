"""`select-field` — read one field from a block, or a flat list of that field
from every iteration of an array.

This is the unified "dot + field" access of the JSON mental model: an object is
a block (read one named field), and a collection is an array of blocks (map the
field over every iteration, like JS ``items.map(x => x.field)``). Nesting is by
chaining — ``select-field "a" | select-field "b"`` is ``obj.a.b``.
"""

from ..navigation import record_navigation_step
from ..registry import cmdlets
from ..value_types import PipeValue


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
    ],
    compact=[{'text': '->', 'role': 'arrow'}, {'arg': 'field'}],
)
def select_field(value: PipeValue, args: dict) -> PipeValue:
    """Return ``block[field]`` for a block, or ``[item[field] …]`` for an array."""
    field = args.get('field')
    if field is None:
        raise ValueError("select-field: missing required arg 'field'")

    if isinstance(value, dict):
        result = _read_field(value, field, 'block')
    elif isinstance(value, list):
        result = [_read_field(item, field, 'array iteration') for item in value]
    else:
        raise TypeError(
            f'select-field: expected a block or an array, got {type(value).__name__}'
        )

    record_navigation_step({'cmdlet': 'select-field', 'args': {'field': field}})
    return result


def _read_field(block, field, what):
    if not isinstance(block, dict):
        raise TypeError(
            f'select-field: {what} must be a block, got {type(block).__name__}'
        )
    if field not in block:
        raise ValueError(f'select-field: field {field!r} not found in {what}')
    return block[field]

"""`literal` — put a fixed constant on one side of a rule."""

from ..registry import cmdlets
from ..value_types import PipeValue, from_serialized


@cmdlets.register(
    'literal',
    kind='source',
    args=[
        {
            'name': 'value',
            'type': 'literal-value',
            'required': True,
            'description': (
                'The fixed constant value — text, number, boolean, path, date, or '
                'raw JSON (array/object). The editor offers a type selector and '
                'stores the value as a typed {type, value} object.'
            ),
        },
    ],
    compact=[{'arg': 'value'}],
    full=[{'arg': 'value'}],
)
def literal(value: PipeValue, args: dict) -> PipeValue:
    """Return the fixed value carried in ``args['value']``.

    This is the canonical way to put a constant (a number, a text, a list, …)
    on the left or right side of a rule. The incoming ``value`` is ignored.
    """
    if 'value' not in args:
        raise ValueError("literal: missing required arg 'value'")
    return from_serialized(args['value'])


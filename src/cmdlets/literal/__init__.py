"""`literal` — put a fixed constant on one side of a rule."""

from ..registry import cmdlets
from ..value_types import PipeValue


@cmdlets.register(
    'literal',
    kind='source',
    args=[
        {
            'name': 'value',
            'type': 'json',
            'required': True,
            'description': 'The fixed constant value (any JSON scalar, array, or object).',
        },
    ],
)
def literal(value: PipeValue, args: dict) -> PipeValue:
    """Return the fixed value carried in ``args['value']``.

    This is the canonical way to put a constant (a number, a text, a list, …)
    on the left or right side of a rule. The incoming ``value`` is ignored.
    """
    if 'value' not in args:
        raise ValueError("literal: missing required arg 'value'")
    return args['value']

"""`count` — count the meaningful entries in the incoming value."""

from ..registry import cmdlets
from ..value_types import Integer, PipeValue, coerce, is_sysmissing


@cmdlets.register(
    'count',
    kind='processor',
    args=[
        {
            'name': 'fail_on_sysmissing',
            'type': 'boolean',
            'required': False,
            'default': False,
            'description': 'Raise instead of returning 0 for a sysmissing value.',
        },
    ],
)
def count(value: PipeValue, args: dict) -> Integer:
    """Count the meaningful entries in the incoming value.

    - collection: number of elements.
    - block: number of fields.
    - multi-punch categorical: number of punched categories.
    - text: ``0`` if empty, ``1`` otherwise.
    - single-punch categorical or any other scalar: ``1`` if a value is stored
      (i.e. it is not ``sysmissing``).
    - ``sysmissing``: ``0`` by default; ``args['fail_on_sysmissing']`` raises.
    """
    value = coerce(value)
    if is_sysmissing(value):
        if bool(args.get('fail_on_sysmissing', False)):
            raise ValueError('count: cannot count a sysmissing value')
        return Integer(0)
    return Integer(value.count())


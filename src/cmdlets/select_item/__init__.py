"""`select-item` — pick one element of a collection by zero-based index.

Selecting an element by *name* is deferred: it needs record/row naming in the
source readers (see "Row & column names" in `docs/cmdlet-data-formats.md`),
which is not implemented yet.
"""

from ..registry import cmdlets
from ..value_types import PipeValue


@cmdlets.register(
    'select-item',
    kind='processor',
    help='Pick one element of a collection by zero-based index.',
    args=[
        {
            'name': 'index',
            'type': 'number',
            'required': True,
            'description': 'Zero-based index (negative counts from the end).',
        },
    ],
)
def select_item(value: PipeValue, args: dict) -> PipeValue:
    """Return ``collection[index]`` (Python indexing semantics, negatives allowed)."""
    if not isinstance(value, list):
        raise TypeError(f'select-item: expected a collection, got {type(value).__name__}')

    index = args.get('index')
    if index is None:
        raise ValueError("select-item: missing required arg 'index'")
    if isinstance(index, bool) or not isinstance(index, int):
        raise TypeError(
            f'select-item: index must be an integer, got {type(index).__name__}'
        )

    try:
        result = value[index]
    except IndexError:
        raise ValueError(
            f'select-item: index {index} out of range for collection of length {len(value)}'
        ) from None

    return result

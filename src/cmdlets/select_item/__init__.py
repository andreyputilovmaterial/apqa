"""`select-item` — pick one element of a collection by zero-based index.

Selecting an element by *name* is deferred: it needs record/row naming in the
source readers (see "Row & column names" in `docs/cmdlet-data-formats.md`),
which is not implemented yet.
"""

from ..registry import cmdlets
from ..value_types import PipeValue, coerce


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
    index = args.get('index')
    if index is None:
        raise ValueError("select-item: missing required arg 'index'")

    return coerce(value).item(index)


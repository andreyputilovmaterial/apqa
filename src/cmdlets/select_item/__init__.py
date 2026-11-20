"""`select-item` — pick one element of a collection by zero-based index.

Selecting an element by *name* is deferred: it needs record/row naming in the
source readers (see "Row & column names" in `docs/cmdlet-data-formats.md`),
which is not implemented yet.

With ``missing_ok: true``, an out-of-range index returns ``sysmissing`` instead
of raising — the JS ``arr[i] === undefined`` behaviour.
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
        {
            'name': 'missing_ok',
            'type': 'boolean',
            'required': False,
            'default': False,
            'description': 'Return sysmissing instead of failing when the index is out of range.',
        },
    ],
)
def select_item(value: PipeValue, args: dict) -> PipeValue:
    """Return ``collection[index]`` (Python indexing semantics, negatives allowed)."""
    index = args.get('index')
    if index is None:
        raise ValueError("select-item: missing required arg 'index'")

    missing_ok = args.get('missing_ok', False)
    return coerce(value).item(index, missing_ok=missing_ok)


"""`sort` — order a collection, optionally by a block field."""

from ..registry import cmdlets
from ..value_types import coerce, is_sysmissing


@cmdlets.register(
    'sort',
    kind='processor',
    args=[
        {'name': 'by', 'type': 'text', 'required': False, 'description': 'Block field to sort by.'},
        {
            'name': 'descending',
            'type': 'boolean',
            'required': False,
            'default': False,
            'description': 'Sort in descending order.',
        },
    ],
)
def sort(value, args):
    """Sort a collection. ``args['by']`` (optional) is the block field to sort
    by; without it a collection of scalars is sorted by its natural order. The
    optional ``args['descending']`` flag reverses the result."""
    value = coerce(value)
    if is_sysmissing(value):
        raise ValueError('sort: cannot sort a sysmissing value')

    by = args.get('by')
    descending = bool(args.get('descending', False))
    return value.sort(by, descending)


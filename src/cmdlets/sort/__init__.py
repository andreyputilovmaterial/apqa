"""`sort` — order an array, optionally by a block field."""

from ..registry import cmdlets
from ..sysmissing import is_sysmissing
from ..value_types import Array


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
def sort(value: Array, args: dict) -> Array:
    """Sort an array. ``args['by']`` (optional) is the block field to sort by;
    without it an array of scalars is sorted by its natural order. The optional
    ``args['descending']`` flag reverses the result."""
    if is_sysmissing(value):
        raise ValueError('sort: cannot sort a sysmissing value')
    if not isinstance(value, list):
        raise TypeError(f'sort: value is not an array: {type(value).__name__}')

    by = args.get('by')
    descending = bool(args.get('descending', False))

    try:
        result = sorted(
            value,
            key=(lambda item: item[by]) if by is not None else None,
        )
    except TypeError as e:
        if by is None:
            raise TypeError(
                'sort: cannot sort an array of blocks without a `by` field'
            ) from e
        raise

    if descending:
        result.reverse()
    return result

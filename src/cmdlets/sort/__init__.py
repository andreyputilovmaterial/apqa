"""`sort` — order a collection, optionally by a block field."""

from ..registry import cmdlets
from ..sysmissing import is_sysmissing
from ..value_types import Collection


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
def sort(value: Collection, args: dict) -> Collection:
    """Sort a collection. ``args['by']`` (optional) is the block field to sort
    by; without it a collection of scalars is sorted by its natural order. The
    optional ``args['descending']`` flag reverses the result."""
    if is_sysmissing(value):
        raise ValueError('sort: cannot sort a sysmissing value')
    if not isinstance(value, list):
        raise TypeError(f'sort: value is not a collection: {type(value).__name__}')

    by = args.get('by')
    descending = bool(args.get('descending', False))
    names = value.names if isinstance(value, Collection) else None

    def key_for(index):
        return value[index][by] if by is not None else value[index]

    try:
        order = sorted(range(len(value)), key=key_for)
    except TypeError as e:
        if by is None:
            raise TypeError(
                'sort: cannot sort a collection of blocks without a `by` field'
            ) from e
        raise

    if descending:
        order.reverse()

    result = [value[index] for index in order]
    if names is not None:
        names = [names[index] for index in order]
    return Collection(result, names)

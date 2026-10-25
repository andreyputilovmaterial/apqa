
from .registry import cmdlets
from .sysmissing import is_sysmissing


@cmdlets.register('literal')
def literal(value, args):
    """Return the fixed value carried in ``args['value']``.

    This is the canonical way to put a constant (a number, a text, a list, …)
    on the left or right side of a rule. The incoming ``value`` is ignored.
    """
    if 'value' not in args:
        raise ValueError("literal: missing required arg 'value'")
    return args['value']


@cmdlets.register('count')
def count(value, args):
    """Return the number of elements in the incoming collection."""
    if is_sysmissing(value):
        raise ValueError('count: cannot count a sysmissing value')
    try:
        return len(value)
    except TypeError as e:
        raise TypeError(
            f'count: value is not countable: {type(value).__name__}'
        ) from e


@cmdlets.register('sort')
def sort(value, args):
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

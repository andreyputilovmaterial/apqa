
from .registry import cmdlets
from .sysmissing import is_sysmissing
from .value_types import Array, PipeValue


@cmdlets.register('literal')
def literal(value: PipeValue, args: dict) -> PipeValue:
    """Return the fixed value carried in ``args['value']``.

    This is the canonical way to put a constant (a number, a text, a list, …)
    on the left or right side of a rule. The incoming ``value`` is ignored.
    """
    if 'value' not in args:
        raise ValueError("literal: missing required arg 'value'")
    return args['value']


@cmdlets.register('count')
def count(value: PipeValue, args: dict) -> int:
    """Count the meaningful entries in the incoming value.

    - array (``list``): number of iterations.
    - block / named collection (``dict``): number of fields.
    - multi-punch categorical: number of punched categories (today a punch list
      is a plain ``list`` and counts as its length, like an array).
    - single-punch categorical, text, or any other scalar: ``1`` if a value is
      stored (i.e. it is not ``sysmissing``). Text is one stored value and is
      not counted character-by-character.
    - ``sysmissing`` (``None``): ``0`` by default; ``args['fail_on_sysmissing']``
      raises instead.
    """
    if is_sysmissing(value):
        if bool(args.get('fail_on_sysmissing', False)):
            raise ValueError('count: cannot count a sysmissing value')
        return 0

    if isinstance(value, str):
        return 1
    if isinstance(value, dict):
        return len(value)
    if isinstance(value, list):
        return len(value)
    return 1


@cmdlets.register('sort')
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

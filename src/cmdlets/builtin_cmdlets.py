
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


from .sysmissing import is_sysmissing


class ComparisonRegistry:
    """Global registry of comparison ops, keyed by op name.

    A comparison op is a plain function ``(left, right) -> bool`` comparing two
    scalars. ``sysmissing`` on either side is handled as "undefined" (see each
    op below). Register an op with ``@comparisons.register('<name>')``.
    """

    def __init__(self):
        self._ops = {}

    def register(self, name):
        def decorator(fn):
            self._ops[name] = fn
            return fn
        return decorator

    def get(self, name):
        if name not in self._ops:
            raise KeyError(f'comparison op not found: {name}')
        return self._ops[name]

    def names(self):
        return list(self._ops)


comparisons = ComparisonRegistry()


@comparisons.register('eq')
def eq(left, right):
    if is_sysmissing(left) or is_sysmissing(right):
        return is_sysmissing(left) and is_sysmissing(right)
    return left == right


@comparisons.register('ne')
def ne(left, right):
    if is_sysmissing(left) or is_sysmissing(right):
        return not (is_sysmissing(left) and is_sysmissing(right))
    return left != right


@comparisons.register('lt')
def lt(left, right):
    if is_sysmissing(left) or is_sysmissing(right):
        return False
    return left < right


@comparisons.register('le')
def le(left, right):
    if is_sysmissing(left) or is_sysmissing(right):
        return False
    return left <= right


@comparisons.register('gt')
def gt(left, right):
    if is_sysmissing(left) or is_sysmissing(right):
        return False
    return left > right


@comparisons.register('ge')
def ge(left, right):
    if is_sysmissing(left) or is_sysmissing(right):
        return False
    return left >= right


@comparisons.register('contains')
def contains(left, right):
    if is_sysmissing(left) or is_sysmissing(right):
        return False
    try:
        return right in left
    except TypeError as e:
        raise TypeError(
            f'contains: left operand does not support containment: '
            f'{type(left).__name__}'
        ) from e

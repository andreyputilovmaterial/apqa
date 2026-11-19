"""`cmp-eq` — deep equality with order-sensitive arrays by default."""

from ..comparison_helpers import is_array, is_block, is_bool, to_number
from ..registry import comparisons
from ..value_types import Boolean, coerce
from ..value_types import is_sysmissing


def _arrays_equal_unordered(left, right, args):
    """Order-agnostic (multiset) array equality under recursive ``eq``."""
    if len(left) != len(right):
        return False
    remaining = list(right)
    for item in left:
        for i, candidate in enumerate(remaining):
            if eq(item, candidate, args):
                remaining.pop(i)
                break
        else:
            return False
    return True


@comparisons.register(
    'cmp-eq',
    help='Equal (deep; arrays order-sensitive unless unordered_arrays).',
    compact=[{'text': '=', 'role': 'symbol'}],
    op_args=[
        {
            'name': 'unordered_arrays',
            'type': 'boolean',
            'required': False,
            'default': False,
            'description': 'Compare arrays as multisets (order does not matter).',
        },
    ],
)
def eq(left, right, args=None):
    left = coerce(left)
    right = coerce(right)
    unordered = bool(args and args.get('unordered_arrays'))
    if is_sysmissing(left) or is_sysmissing(right):
        return is_sysmissing(left) and is_sysmissing(right)
    if is_block(left) or is_block(right):
        return (
            is_block(left) and is_block(right)
            and left.keys() == right.keys()
            and all(eq(left[key], right[key], args) for key in left)
        )
    if is_array(left) or is_array(right):
        if not (is_array(left) and is_array(right)):
            return False
        if unordered:
            return _arrays_equal_unordered(left, right, args)
        return (
            len(left) == len(right)
            and all(eq(a, b, args) for a, b in zip(left, right))
        )
    if is_bool(left) or is_bool(right):
        return is_bool(left) and is_bool(right) and left.value == right.value
    left_num = to_number(left)
    right_num = to_number(right)
    if left_num is not None and right_num is not None:
        return left_num == right_num
    if left_num is not None or right_num is not None:
        return False
    return left == right


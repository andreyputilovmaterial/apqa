"""`cmp-contains` — membership (substring for text, membership for arrays)."""

from ..registry import comparisons
from ..value_types import Text, coerce, is_sysmissing


@comparisons.register(
    'cmp-contains',
    help='Membership (substring for text, membership for arrays).',
)
def contains(left, right, args=None):
    left = coerce(left)
    right = coerce(right)
    if is_sysmissing(left) or is_sysmissing(right):
        return False
    if isinstance(left, Text):
        if not isinstance(right, Text):
            return False
        return right.value in left.value
    try:
        return right in left
    except TypeError:
        return False


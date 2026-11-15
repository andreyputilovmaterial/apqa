"""`cmp-contains` — membership (substring for text, membership for arrays)."""

from ..registry import comparisons
from ..sysmissing import is_sysmissing


@comparisons.register(
    'cmp-contains',
    help='Membership (substring for text, membership for arrays).',
)
def contains(left, right, args=None):
    if is_sysmissing(left) or is_sysmissing(right):
        return False
    try:
        return right in left
    except TypeError:
        return False

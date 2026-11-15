"""`cmp-gt` — greater than (scalar only)."""

import operator

from ..comparison_helpers import ordered_compare
from ..registry import comparisons


@comparisons.register(
    'cmp-gt',
    help='Greater than (scalar only).',
    compact=[{'text': '>', 'role': 'symbol'}],
)
def gt(left, right, args=None):
    return ordered_compare(operator.gt, left, right)

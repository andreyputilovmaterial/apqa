"""`cmp-lt` — less than (scalar only)."""

import operator

from ..comparison_helpers import ordered_compare
from ..registry import comparisons


@comparisons.register(
    'cmp-lt',
    help='Less than (scalar only).',
    compact=[{'text': '<', 'role': 'symbol'}],
)
def lt(left, right, args=None):
    return ordered_compare(operator.lt, left, right)

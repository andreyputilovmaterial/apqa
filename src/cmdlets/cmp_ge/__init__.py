"""`cmp-ge` — greater than or equal (scalar only)."""

import operator

from ..comparison_helpers import ordered_compare
from ..registry import comparisons


@comparisons.register(
    'cmp-ge',
    help='Greater than or equal (scalar only).',
    compact=[{'text': '≥', 'role': 'symbol'}],
)
def ge(left, right, args=None):
    return ordered_compare(operator.ge, left, right)

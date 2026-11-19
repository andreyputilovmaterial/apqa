"""`cmp-le` — less than or equal (scalar only)."""

import operator

from ..comparison_helpers import ordered_compare
from ..registry import comparisons
from ..value_types import coerce


@comparisons.register(
    'cmp-le',
    help='Less than or equal (scalar only).',
    compact=[{'text': '≤', 'role': 'symbol'}],
)
def le(left, right, args=None):
    return ordered_compare(operator.le, coerce(left), coerce(right))


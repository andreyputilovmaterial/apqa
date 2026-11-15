"""`cmp-eq-unordered` — ``cmp-eq`` with order-agnostic arrays hard-wired."""

from ..cmp_eq import eq
from ..registry import comparisons


@comparisons.register('cmp-eq-unordered', help='Equal with order-agnostic arrays.')
def eq_unordered(left, right, args=None):
    return eq(left, right, {'unordered_arrays': True})

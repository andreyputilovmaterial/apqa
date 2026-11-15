"""`cmp-ne` — negation of ``cmp-eq``."""

from ..cmp_eq import eq
from ..registry import comparisons


@comparisons.register(
    'cmp-ne',
    help='Not equal.',
    compact=[{'text': '≠', 'role': 'symbol'}],
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
def ne(left, right, args=None):
    return not eq(left, right, args)

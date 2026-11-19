"""`select-range` — take a sub-range of a collection.

Mirrors Python slice ``collection[start:stop]``: ``start`` is inclusive, ``stop`` is
exclusive, both may be omitted (open-ended), and there is no step. Negative
indices count from the end, exactly like Python.
"""

from ..registry import cmdlets
from ..value_types import PipeValue, coerce


@cmdlets.register(
    'select-range',
    kind='processor',
    help='Take a sub-range of a collection: start inclusive, stop exclusive.',
    args=[
        {
            'name': 'start',
            'type': 'number',
            'required': False,
            'description': 'First index to include (0-based; omitted = from the start).',
        },
        {
            'name': 'stop',
            'type': 'number',
            'required': False,
            'description': 'First index to exclude (exclusive; omitted = to the end).',
        },
    ],
)
def select_range(value: PipeValue, args: dict) -> PipeValue:
    """Return ``collection[start:stop]`` (Python slice semantics, no step)."""
    return coerce(value).slice(args.get('start'), args.get('stop'))


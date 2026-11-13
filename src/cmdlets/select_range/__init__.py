"""`select-range` — take a sub-range of an array.

Mirrors Python slice ``array[start:stop]``: ``start`` is inclusive, ``stop`` is
exclusive, both may be omitted (open-ended), and there is no step. Negative
indices count from the end, exactly like Python.
"""

from ..registry import cmdlets
from ..value_types import Array, PipeValue


@cmdlets.register(
    'select-range',
    kind='processor',
    help='Take a sub-range of an array: start inclusive, stop exclusive.',
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
def select_range(value: PipeValue, args: dict) -> Array:
    """Return ``array[start:stop]`` (Python slice semantics, no step)."""
    if not isinstance(value, list):
        raise TypeError(f'select-range: expected an array, got {type(value).__name__}')

    start = _slice_index(args.get('start'), 'start')
    stop = _slice_index(args.get('stop'), 'stop')
    return value[start:stop]


def _slice_index(value, name):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(
            f'select-range: {name} must be an integer or omitted, got '
            f'{type(value).__name__}'
        )
    return value

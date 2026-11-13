"""`map` — transform every iteration of an array with a cmdlet chain.

`map` is ForEach-Object: its ``transform`` argument is a **cmdlet chain** run
once per iteration, with the iteration threaded through as the piped value (a
JS ``items.map(x => …)``). The result is an array of the transformed values.
"""

from ..chain_runner import run_chain
from ..registry import cmdlets
from ..value_types import Array, PipeValue


@cmdlets.register(
    'map',
    kind='processor',
    help='Transform every iteration of an array with a cmdlet chain.',
    args=[
        {
            'name': 'transform',
            'type': 'cmdlet-chain',
            'required': True,
            'description': 'Cmdlet chain run once per iteration (the iteration is its piped input).',
        },
    ],
)
def map_(value: PipeValue, args: dict) -> Array:
    """Return ``[run_chain(transform, initial=item) for item in value]``."""
    if not isinstance(value, list):
        raise TypeError(f'map: expected an array, got {type(value).__name__}')

    transform = args.get('transform')
    if not isinstance(transform, list) or not transform:
        raise ValueError(
            "map: missing required arg 'transform' (a non-empty cmdlet chain)"
        )

    return [run_chain(transform, initial=item) for item in value]

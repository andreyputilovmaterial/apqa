"""`foreach-item` — transform every item of an array with a cmdlet chain.

`foreach-item` is ForEach-Object: its ``transform`` argument is a **cmdlet
chain** run once per item, with the item threaded through as the piped value (a
JS ``items.map(x => …)``). The result is an array of the transformed values.
"""

from ..chain_runner import run_chain
from ..registry import cmdlets
from ..value_types import Array, PipeValue


@cmdlets.register(
    'foreach-item',
    kind='processor',
    help='Transform every item of an array with a cmdlet chain.',
    args=[
        {
            'name': 'transform',
            'type': 'cmdlet-chain',
            'required': True,
            'description': 'Cmdlet chain run once per item (the item is its piped input).',
        },
    ],
)
def foreach_item(value: PipeValue, args: dict) -> Array:
    """Return ``[run_chain(transform, initial=item) for item in value]``."""
    if not isinstance(value, list):
        raise TypeError(f'foreach-item: expected an array, got {type(value).__name__}')

    transform = args.get('transform')
    if not isinstance(transform, list) or not transform:
        raise ValueError(
            "foreach-item: missing required arg 'transform' (a non-empty cmdlet chain)"
        )

    return [run_chain(transform, initial=item) for item in value]

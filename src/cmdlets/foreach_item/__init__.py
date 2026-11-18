"""`foreach-item` — transform every item of a collection with a cmdlet chain.

`foreach-item` is ForEach-Object: its ``transform`` argument is a **cmdlet
chain** run once per item, with the item threaded through as the piped value (a
JS ``items.map(x => …)``). The result is a collection of the transformed values.
"""

from ..chain_runner import run_chain
from ..registry import cmdlets
from ..value_types import Collection, PipeValue


@cmdlets.register(
    'foreach-item',
    kind='processor',
    help='Transform every item of a collection with a cmdlet chain.',
    args=[
        {
            'name': 'transform',
            'type': 'cmdlet-chain',
            'required': True,
            'description': 'Cmdlet chain run once per item (the item is its piped input).',
        },
    ],
)
def foreach_item(value: PipeValue, args: dict) -> Collection:
    """Return a collection of ``run_chain(transform, initial=item)`` per item."""
    if not isinstance(value, list):
        raise TypeError(f'foreach-item: expected a collection, got {type(value).__name__}')

    transform = args.get('transform')
    if not isinstance(transform, list) or not transform:
        raise ValueError(
            "foreach-item: missing required arg 'transform' (a non-empty cmdlet chain)"
        )

    names = value.names if isinstance(value, Collection) else None
    return Collection(
        [run_chain(transform, initial=item) for item in value],
        names,
    )

"""`foreach-field` — transform every own field of a block with a cmdlet chain.

`foreach-field` is `foreach-item` for blocks instead of arrays: its ``transform``
argument is a **cmdlet chain** run once per own field, with the field's value
threaded through as the piped value. The result is a block with the same field
names and the transformed values. It steps over the block's **own** fields only
and does not recurse — use `foreach-deep-node` to walk the whole tree.
"""

from ..chain_runner import run_chain
from ..registry import cmdlets
from ..value_types import Block, PipeValue


@cmdlets.register(
    'foreach-field',
    kind='processor',
    help='Transform every field of a block with a cmdlet chain.',
    args=[
        {
            'name': 'transform',
            'type': 'cmdlet-chain',
            'required': True,
            'description': 'Cmdlet chain run once per field (the field value is its piped input).',
        },
    ],
)
def foreach_field(value: PipeValue, args: dict) -> Block:
    """Return ``{key: run_chain(transform, initial=field) for key, field in value.items()}``."""
    if not isinstance(value, dict):
        raise TypeError(f'foreach-field: expected a block, got {type(value).__name__}')

    transform = args.get('transform')
    if not isinstance(transform, list) or not transform:
        raise ValueError(
            "foreach-field: missing required arg 'transform' (a non-empty cmdlet chain)"
        )

    return {key: run_chain(transform, initial=field) for key, field in value.items()}

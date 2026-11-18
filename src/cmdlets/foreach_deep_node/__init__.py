"""`foreach-deep-node` — transform every scalar leaf of the piped value.

`foreach-deep-node` is `foreach-field` recursing through the whole tree: its
``transform`` argument is a **cmdlet chain** run once per scalar leaf (including
``sysmissing``), with the leaf threaded through as the piped value. Blocks and
arrays are kept as scaffolding and rebuilt in the same shape, so only the leaves
change:

    get-content-mdd path=… -> foreach-deep-node transform=[…] -> …

This is the generic, chain-parameterized form of the recursive walk
`transform-strip-html` does with a fixed operation.
"""

from ..chain_runner import run_chain
from ..diagnostic import note_path_prefix
from ..registry import cmdlets
from ..value_types import Block, Collection, PipeValue


@cmdlets.register(
    'foreach-deep-node',
    kind='processor',
    help='Transform every scalar leaf of the piped value with a cmdlet chain.',
    args=[
        {
            'name': 'transform',
            'type': 'cmdlet-chain',
            'required': True,
            'description': 'Cmdlet chain run once per scalar leaf (the leaf is its piped input).',
        },
    ],
)
def foreach_deep_node(value: PipeValue, args: dict) -> PipeValue:
    """Return the tree with every scalar leaf replaced by ``run_chain(transform, initial=leaf)``."""
    transform = args.get('transform')
    if not isinstance(transform, list) or not transform:
        raise ValueError(
            "foreach-deep-node: missing required arg 'transform' (a non-empty cmdlet chain)"
        )

    return _map_leaves(value, transform, [])


def _map_leaves(value, transform, path):
    if isinstance(value, dict):
        return Block({
            key: _map_leaves(child, transform, path + [key])
            for key, child in value.items()
        })
    if isinstance(value, list):
        names = value.names if isinstance(value, Collection) else None
        return Collection(
            [
                _map_leaves(child, transform, path + [index])
                for index, child in enumerate(value)
            ],
            names,
        )
    with note_path_prefix(path):
        return run_chain(transform, initial=value)

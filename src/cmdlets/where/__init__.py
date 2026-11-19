"""`where` — keep the iterations of a collection whose predicate chain is truthy.

`where` is Where-Object: its ``predicate`` argument is a **cmdlet chain** run
once per iteration, with the iteration threaded through as the piped value (a
JS ``items.filter(x => …)``). An iteration is kept when the chain's result is
truthy (``bool(result)``, so ``sysmissing`` counts as ``False`` — the same
coercion as `and`/`or`/`any`/`all`).
"""

from ..chain_runner import run_chain
from ..registry import cmdlets
from ..value_types import PipeValue, coerce


@cmdlets.register(
    'where',
    kind='processor',
    help='Keep the iterations of a collection whose predicate chain is truthy.',
    args=[
        {
            'name': 'predicate',
            'type': 'cmdlet-chain',
            'required': True,
            'description': 'Cmdlet chain run once per iteration; the iteration is kept when its result is truthy.',
        },
    ],
)
def where(value: PipeValue, args: dict) -> PipeValue:
    """Return a collection of the items whose predicate chain is truthy."""
    predicate = args.get('predicate')
    if not isinstance(predicate, list) or not predicate:
        raise ValueError(
            "where: missing required arg 'predicate' (a non-empty cmdlet chain)"
        )

    value = coerce(value)
    return value.filter(lambda item: bool(run_chain(predicate, initial=item)))


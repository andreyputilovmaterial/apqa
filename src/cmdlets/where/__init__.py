"""`where` — keep the iterations of an array whose predicate chain is truthy.

`where` is Where-Object: its ``predicate`` argument is a **cmdlet chain** run
once per iteration, with the iteration threaded through as the piped value (a
JS ``items.filter(x => …)``). An iteration is kept when the chain's result is
truthy (``bool(result)``, so ``sysmissing`` counts as ``False`` — the same
coercion as `and`/`or`/`any`/`all`).

For now the predicate is limited to the existing predicate/validation cmdlets
(`is-sysmissing`, `not`, `and`, `or`, `validate-*`, or the truthiness of a
field); comparison-as-cmdlet (e.g. `eq`) is tracked in `docs/roadmap.md`.
"""

from ..chain_runner import run_chain
from ..registry import cmdlets
from ..value_types import Array, PipeValue


@cmdlets.register(
    'where',
    kind='processor',
    help='Keep the iterations of an array whose predicate chain is truthy.',
    args=[
        {
            'name': 'predicate',
            'type': 'cmdlet-chain',
            'required': True,
            'description': 'Cmdlet chain run once per iteration; the iteration is kept when its result is truthy.',
        },
    ],
)
def where(value: PipeValue, args: dict) -> Array:
    """Return ``[item for item in value if bool(run_chain(predicate, initial=item))]``."""
    if not isinstance(value, list):
        raise TypeError(f'where: expected an array, got {type(value).__name__}')

    predicate = args.get('predicate')
    if not isinstance(predicate, list) or not predicate:
        raise ValueError(
            "where: missing required arg 'predicate' (a non-empty cmdlet chain)"
        )

    return [item for item in value if bool(run_chain(predicate, initial=item))]

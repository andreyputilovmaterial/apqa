"""`where` — keep the iterations of a collection whose predicate chain is truthy.

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
from ..value_types import Collection, PipeValue


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
def where(value: PipeValue, args: dict) -> Collection:
    """Return a collection of the items whose predicate chain is truthy."""
    if not isinstance(value, list):
        raise TypeError(f'where: expected a collection, got {type(value).__name__}')

    predicate = args.get('predicate')
    if not isinstance(predicate, list) or not predicate:
        raise ValueError(
            "where: missing required arg 'predicate' (a non-empty cmdlet chain)"
        )

    names = value.names if isinstance(value, Collection) else None
    kept = []
    kept_names = []
    for index, item in enumerate(value):
        if bool(run_chain(predicate, initial=item)):
            kept.append(item)
            if names is not None:
                kept_names.append(names[index])
    return Collection(kept, kept_names if names is not None else None)

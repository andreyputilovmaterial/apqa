"""`include-child` — keep only the matching direct children of the piped value.

The inverse of `exclude-child`: it keeps the direct children of the received
block/array whose **key/index** matches a rule in ``rules`` and drops the rest.
It does not recurse into the kept children.

Each child is matched by its one-segment data path rendered by ``format_path``
(a block key is its name, an array element is ``[i]``), so ``rules`` uses the
same shape as `include-deep-node`:

    get-content-mdd path=… -> include-child rules=[{type: startswith, pattern: Sniffer}] -> …

Returns ``None`` (sysmissing) when no child is kept.
"""

from ..diagnostic import format_path
from ..path_rules import matches_any_rule, normalize_rules
from ..registry import cmdlets
from ..value_types import Collection, PipeValue


@cmdlets.register(
    'include-child',
    kind='processor',
    help='Keep only the direct children of the piped value whose key/index matches a rule.',
    args=[
        {
            'name': 'rules',
            'type': 'path-rules',
            'required': True,
            'description': 'Rules matching direct-child paths to keep, e.g. {type: eq, pattern: Select}.',
        },
    ],
)
def include_child(value: PipeValue, args: dict) -> PipeValue:
    """Keep matching direct children of a block or an array."""
    rules = normalize_rules(args.get('rules'))

    if isinstance(value, dict):
        kept = {
            key: child
            for key, child in value.items()
            if matches_any_rule(format_path([key]), rules)
        }
        return kept if kept else None
    if isinstance(value, list):
        names = value.names if isinstance(value, Collection) else None
        kept = []
        kept_names = []
        for index, child in enumerate(value):
            if matches_any_rule(format_path([index]), rules):
                kept.append(child)
                if names is not None:
                    kept_names.append(names[index])
        if not kept:
            return None
        return Collection(kept, kept_names if names is not None else None)
    return None

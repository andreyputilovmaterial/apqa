"""`include-deep-node` — keep only the nodes of the piped value whose path matches.

The inverse of `exclude-deep-node`: it recursively walks the received block /
array and keeps a node when its **data path relative to the received value**
matches a rule in ``rules``, plus every ancestor needed to reach it. Everything
else is dropped:

    get-content-mdd path=… -> include-deep-node rules=[{type: endswith, pattern: .Label}] -> validate-xml-compatible cmp-eq literal(True)

A matched node is kept **with its whole subtree**; an unmatched container
survives only as scaffolding for a matching descendant (empty containers that
lead to no match are dropped). Matching is relative to whatever the cmdlet
receives, so it can sit anywhere in a chain. Returns ``None`` (sysmissing) when
nothing is kept.
"""

from ..diagnostic import format_path
from ..path_rules import matches_any_rule, normalize_rules
from ..registry import cmdlets
from ..value_types import Collection, PipeValue


_REMOVED = object()


@cmdlets.register(
    'include-deep-node',
    kind='processor',
    help='Keep only the nodes of the piped value whose data path matches a rule.',
    args=[
        {
            'name': 'rules',
            'type': 'path-rules',
            'required': True,
            'description': 'Rules matching data paths (relative to the piped value) to keep.',
        },
    ],
)
def include_deep_node(value: PipeValue, args: dict) -> PipeValue:
    """Keep matching nodes (and their scaffolding), dropping everything else."""
    rules = normalize_rules(args.get('rules'))
    kept = _keep(value, [], rules)
    return None if kept is _REMOVED else kept


def _keep(value, path, rules):
    """Return ``value`` pruned to matching nodes, or ``_REMOVED`` when empty.

    A node whose path matches a rule is kept whole; a container that does not
    match is kept only when it has at least one kept descendant, and then only
    with those kept descendants. Scalars that do not match are removed.
    """
    if matches_any_rule(format_path(path), rules):
        return value
    if isinstance(value, dict):
        kept = {}
        for key, child in value.items():
            child_result = _keep(child, path + [key], rules)
            if child_result is not _REMOVED:
                kept[key] = child_result
        return kept if kept else _REMOVED
    if isinstance(value, list):
        names = value.names if isinstance(value, Collection) else None
        kept = []
        kept_names = []
        for index, child in enumerate(value):
            child_result = _keep(child, path + [index], rules)
            if child_result is not _REMOVED:
                kept.append(child_result)
                if names is not None:
                    kept_names.append(names[index])
        if not kept:
            return _REMOVED
        return Collection(kept, kept_names if names is not None else None)
    return _REMOVED

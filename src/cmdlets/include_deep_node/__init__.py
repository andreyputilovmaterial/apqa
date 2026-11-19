"""`include-deep-node` — keep only the nodes of the piped value whose path matches.

The inverse of `exclude-deep-node`: it recursively walks the received block /
collection and keeps a node when its **data path relative to the received value**
matches a rule in ``rules``, plus every ancestor needed to reach it. Everything
else is dropped:

    get-content-mdd path=… -> include-deep-node rules=[{type: endswith, pattern: .Label}] -> …

A matched node is kept **with its whole subtree**; an unmatched container
survives only as scaffolding for a matching descendant (empty containers that
lead to no match are dropped). Matching is relative to whatever the cmdlet
receives, so it can sit anywhere in a chain. Returns ``sysmissing`` when nothing
is kept.
"""

from ..path_rules import normalize_rules, path_matches
from ..registry import cmdlets
from ..value_types import Block, Collection, PipeValue, coerce, sysmissing


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
    kept = _keep(coerce(value), [], [], rules)
    return sysmissing if kept is _REMOVED else kept


def _keep(value, index_path, name_path, rules):
    """Return ``value`` pruned to matching nodes, or ``_REMOVED`` when empty.

    ``index_path``/``name_path`` are the two spellings of the path leading to
    ``value``; a node matches when either spelling matches a rule. A matched
    node is kept whole; a container that does not match is kept only when it has
    at least one kept descendant. Scalars that do not match are removed.
    """
    if path_matches(index_path, name_path, rules):
        return value
    if isinstance(value, Block):
        kept = Block()
        for key, child in value.items():
            child_result = _keep(child, index_path + [key], name_path + [key], rules)
            if child_result is not _REMOVED:
                kept[key] = child_result
        return kept if kept else _REMOVED
    if isinstance(value, Collection):
        kept = []
        kept_names = []
        for index, (child, child_index, child_name) in enumerate(
            value.iter_child_paths(index_path, name_path)
        ):
            child_result = _keep(child, child_index, child_name, rules)
            if child_result is not _REMOVED:
                kept.append(child_result)
                kept_names.append(value.names[index])
        if not kept:
            return _REMOVED
        return Collection(kept, kept_names)
    return _REMOVED


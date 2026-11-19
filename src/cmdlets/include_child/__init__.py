"""`include-child` — keep only the matching direct children of the piped value.

The inverse of `exclude-child`: it keeps the direct children of the received
block/collection whose **key/index** matches a rule in ``rules`` and drops the
rest. It does not recurse into the kept children.

Each child is matched by its one-segment data path rendered by ``format_path``
(a block key is its name, a collection element is ``[i]``), so ``rules`` uses the
same shape as `include-deep-node`:

    get-content-mdd path=… -> include-child rules=[{type: startswith, pattern: Sniffer}] -> …

Returns ``sysmissing`` when no child is kept.
"""

from ..path_rules import normalize_rules, path_matches
from ..registry import cmdlets
from ..value_types import Block, Collection, PipeValue, coerce, sysmissing


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
    """Keep matching direct children of a block or a collection."""
    rules = normalize_rules(args.get('rules'))
    value = coerce(value)

    if isinstance(value, Block):
        kept = Block({
            key: child
            for key, child in value.items()
            if path_matches([key], [key], rules)
        })
        return kept if kept else sysmissing
    if isinstance(value, Collection):
        kept = []
        kept_names = []
        for index, (child, child_index, child_name) in enumerate(
            value.iter_child_paths([], [])
        ):
            if path_matches(child_index, child_name, rules):
                kept.append(child)
                kept_names.append(value.names[index])
        if not kept:
            return sysmissing
        return Collection(kept, kept_names)
    return sysmissing


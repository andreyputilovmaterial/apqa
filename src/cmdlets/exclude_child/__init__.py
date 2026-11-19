"""`exclude-child` — remove matching direct children of the piped value.

A shallow sibling of `exclude-deep-node`: it looks only at the direct children
of the received block/collection and removes those whose **key/index** matches a
rule in ``rules``. It does not recurse into the children that stay.

Each child is matched by its one-segment data path rendered by ``format_path``
(a block key is its name, a collection element is ``[i]``), so ``rules`` uses the
same shape as `exclude-deep-node`:

    get-content-mdd path=… -> exclude-child rules=[{type: eq, pattern: Fields}] -> …
"""

from ..path_rules import normalize_rules, path_matches
from ..registry import cmdlets
from ..value_types import Block, Collection, PipeValue, coerce


@cmdlets.register(
    'exclude-child',
    kind='processor',
    help='Remove the direct children of the piped value whose key/index matches a rule.',
    args=[
        {
            'name': 'rules',
            'type': 'path-rules',
            'required': True,
            'description': 'Rules matching direct-child paths to remove, e.g. {type: eq, pattern: Select}.',
        },
    ],
)
def exclude_child(value: PipeValue, args: dict) -> PipeValue:
    """Remove matching direct children of a block or a collection."""
    rules = normalize_rules(args.get('rules'))
    value = coerce(value)

    if isinstance(value, Block):
        return Block({
            key: child
            for key, child in value.items()
            if not path_matches([key], [key], rules)
        })
    if isinstance(value, Collection):
        kept = []
        kept_names = []
        for index, (child, child_index, child_name) in enumerate(
            value.iter_child_paths([], [])
        ):
            if not path_matches(child_index, child_name, rules):
                kept.append(child)
                kept_names.append(value.names[index])
        return Collection(kept, kept_names)
    return value


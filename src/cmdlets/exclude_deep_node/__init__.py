"""`exclude-deep-node` — remove nodes from the piped value by their data path.

Replaces the former `filter` cmdlet. It recursively walks the received block /
array and removes every node whose **data path relative to the received value**
matches a rule in ``rules``, passing everything else through unchanged:

    get-content-mdd path=… -> exclude-deep-node rules=[…] -> validate-xml-compatible cmp-eq literal(True)

Because it matches *relative* paths, the same cmdlet works anywhere in a chain:
each rule is written against whatever the cmdlet receives, not the root. The
received value itself is never removed; only nodes beneath it are candidates.

``rules`` is a list of rule mappings (see ``src/cmdlets/path_rules.py``); each
rule matches a node's rendered path (``format_path`` notation, e.g.
``Fields.SnifferData.Fields.Cluster.Categories.Select``). A path naming a block
key or an array element removes that whole node; a path naming a leaf removes
just that leaf; a path matching no node is ignored.
"""

from ..path_rules import iter_child_paths, normalize_rules, path_matches
from ..registry import cmdlets
from ..value_types import Collection, PipeValue


@cmdlets.register(
    'exclude-deep-node',
    kind='processor',
    help='Recursively remove nodes from the piped value whose data path matches a rule.',
    args=[
        {
            'name': 'rules',
            'type': 'path-rules',
            'required': True,
            'description': 'Rules matching data paths (relative to the piped value) to remove.',
        },
    ],
)
def exclude_deep_node(value: PipeValue, args: dict) -> PipeValue:
    """Remove every node whose relative path matches a rule."""
    rules = normalize_rules(args.get('rules'))
    return _prune(value, [], [], rules)


def _prune(value, index_path, name_path, rules):
    """Remove every child node whose relative path matches a rule.

    ``index_path``/``name_path`` are the two spellings of the path leading to
    ``value`` (collection elements are spelled ``[i]`` by index and ``.Name`` by
    name). A child matches when either spelling matches a rule; otherwise the
    walk continues into it. Blocks are pruned in place; collections are rebuilt
    so their names stay consistent.
    """
    if isinstance(value, dict):
        for key in list(value.keys()):
            child_index = index_path + [key]
            child_name = name_path + [key]
            if path_matches(child_index, child_name, rules):
                del value[key]
            else:
                value[key] = _prune(value[key], child_index, child_name, rules)
        return value
    if isinstance(value, list):
        names = value.names if isinstance(value, Collection) else None
        kept = []
        kept_names = []
        for index, (child, child_index, child_name) in enumerate(
            iter_child_paths(value, index_path, name_path)
        ):
            if not path_matches(child_index, child_name, rules):
                kept.append(_prune(child, child_index, child_name, rules))
                if names is not None:
                    kept_names.append(names[index])
        return Collection(kept, kept_names if names is not None else None)
    return value

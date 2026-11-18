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

from ..diagnostic import format_path
from ..path_rules import matches_any_rule, normalize_rules
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
    """Remove, in place, every node whose relative path matches a rule."""
    rules = normalize_rules(args.get('rules'))
    return _prune(value, [], rules)


def _prune(value, path, rules):
    """Remove every child node whose relative path matches a rule.

    ``path`` is the list of segments (keys/indices) leading to ``value``,
    relative to the value the cmdlet received. A child's path is
    ``format_path(path + [key])``; when it matches, the child is deleted,
    otherwise the walk continues into it. List elements are walked from the end
    so deletions do not shift unprocessed indices.
    """
    if isinstance(value, dict):
        for key in list(value.keys()):
            child_path = path + [key]
            if matches_any_rule(format_path(child_path), rules):
                del value[key]
            else:
                value[key] = _prune(value[key], child_path, rules)
        return value
    if isinstance(value, list):
        names = value.names if isinstance(value, Collection) else None
        kept = []
        kept_names = []
        for index, child in enumerate(value):
            child_path = path + [index]
            if not matches_any_rule(format_path(child_path), rules):
                kept.append(_prune(child, child_path, rules))
                if names is not None:
                    kept_names.append(names[index])
        return Collection(kept, kept_names if names is not None else None)
    return value

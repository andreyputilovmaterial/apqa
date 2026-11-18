"""`exclude-child` — remove matching direct children of the piped value.

A shallow sibling of `exclude-deep-node`: it looks only at the direct children
of the received block/array and removes those whose **key/index** matches a rule
in ``rules``. It does not recurse into the children that stay.

Each child is matched by its one-segment data path rendered by ``format_path``
(a block key is its name, an array element is ``[i]``), so ``rules`` uses the
same shape as `exclude-deep-node`:

    get-content-mdd path=… -> exclude-child rules=[{type: eq, pattern: Fields}] -> validate-xml-compatible cmp-eq literal(True)
"""

from ..diagnostic import format_path
from ..path_rules import matches_any_rule, normalize_rules
from ..registry import cmdlets
from ..value_types import Collection, PipeValue


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
    """Remove matching direct children of a block or an array."""
    rules = normalize_rules(args.get('rules'))

    if isinstance(value, dict):
        return {
            key: child
            for key, child in value.items()
            if not matches_any_rule(format_path([key]), rules)
        }
    if isinstance(value, list):
        names = value.names if isinstance(value, Collection) else None
        kept = []
        kept_names = []
        for index, child in enumerate(value):
            if not matches_any_rule(format_path([index]), rules):
                kept.append(child)
                if names is not None:
                    kept_names.append(names[index])
        return Collection(kept, kept_names if names is not None else None)
    return value

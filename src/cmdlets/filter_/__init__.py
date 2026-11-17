"""`filter` — remove nodes from the piped input by their full data path.

The input can be a deep, nested structure (an MDD metadata block, an Excel
workbook, …). `filter` is a processor that removes from that structure the
nodes whose **data path** — the sequence of block keys and array indices from
the root value to the node — is listed in its ``ignorelist`` argument, and
passes everything else through unchanged:

    get-content-mdd path=… -> filter ignorelist=[…] -> validate-xml-compatible cmp-eq literal(True)

Because the navigation path is tracked per chain (see
``src/cmdlets/navigation.py``), `filter` can sit **anywhere** in the chain: each
``ignorelist`` entry is a full path from the root, and the filter prepends the
prefix it has already travelled to every node it walks before matching.

``ignorelist`` is a list of path **strings**, rendered in the same notation the
diagnostic notes use (``format_path``): block keys joined with ``.``, array
indices as ``[i]``, non-identifier keys quoted (``['None of the above']``), e.g.
``Fields.SnifferData.Fields.Cluster.Categories.Select`` or
``Pages.Q1.value[2].Label``.

A path naming a block key or an array element removes that whole node; a path
naming a leaf removes just that leaf; a path equal to the filter's own position
removes the whole received value (the filter returns ``None``). A path matching
no node under the received value is ignored.
"""

from ..diagnostic import format_path
from ..navigation import current_navigation
from ..registry import cmdlets
from ..value_types import PipeValue


@cmdlets.register(
    'filter',
    kind='processor',
    help='Remove nodes from the piped input by their full data path.',
    args=[
        {
            'name': 'ignorelist',
            'type': 'strings',
            'required': True,
            'description': 'Full paths to remove, e.g. Fields.SnifferData.Fields.Cluster.Categories.Select.',
        },
    ],
)
def filter_(value: PipeValue, args: dict) -> PipeValue:
    ignorelist = args.get('ignorelist') or []
    if not isinstance(ignorelist, list):
        raise TypeError("filter: 'ignorelist' must be a list of path strings")

    ignore = set()
    for path in ignorelist:
        if not isinstance(path, str) or not path:
            raise ValueError('filter: each path must be a non-empty string')
        ignore.add(path)

    prefix = _prefix_segments(current_navigation())
    if format_path(prefix) in ignore:
        return None

    return _prune(value, prefix, ignore)


def _prefix_segments(steps):
    """The data-path prefix contributed by the navigating steps applied so far.

    ``select-field`` contributes its field name, ``select-item`` its index; any
    other (future) step kind contributes nothing to a *data* path.
    """
    segments = []
    for step in steps:
        cmdlet = step.get('cmdlet')
        args = step.get('args') or {}
        if cmdlet == 'select-field':
            segments.append(args.get('field'))
        elif cmdlet == 'select-item':
            segments.append(args.get('index'))
    return segments


def _prune(value, path, ignore):
    """Remove, in place, every node whose full path is in ``ignore``.

    ``path`` is the list of segments (keys/indices) leading to ``value``. A
    child's full path is ``format_path(path + [key])``; when it is ignored the
    child is deleted, otherwise the walk continues into it. List elements are
    walked from the end so deletions do not shift unprocessed indices.
    """
    if isinstance(value, dict):
        for key in list(value.keys()):
            child_path = path + [key]
            if format_path(child_path) in ignore:
                del value[key]
            else:
                value[key] = _prune(value[key], child_path, ignore)
        return value
    if isinstance(value, list):
        for index in reversed(range(len(value))):
            child_path = path + [index]
            if format_path(child_path) in ignore:
                del value[index]
            else:
                value[index] = _prune(value[index], child_path, ignore)
        return value
    return value
"""Helpers for walking the runtime compound value tree (blocks and arrays).

The runtime value taxonomy (see ``value_types.py``) has exactly two compound
shapes: a block (``dict``) and an array (``list``). Everything else — including
``sysmissing`` (``None``) — is a scalar leaf. These helpers enumerate the leaves
depth-first so cmdlets that reduce a whole value (``logical-all`` and friends)
can evaluate every field/item without special-casing the shape.
"""


def iter_leaves(value):
    """Yield every scalar leaf of ``value``, traversing blocks and arrays."""
    if isinstance(value, dict):
        for child in value.values():
            yield from iter_leaves(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_leaves(child)
    else:
        yield value

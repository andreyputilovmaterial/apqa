"""Compound value classes: blocks and collections."""

from .base import Compound

__all__ = ['Block', 'Collection']


class Block(Compound, dict):
    """A block: the named fields of an object (a ``dict`` subclass).

    Fields are addressed by name (``block['field']`` / ``block.field('field')``).
    Because a ``dict`` preserves insertion order, a field can also be read by its
    0-based position via :meth:`child_at` — a positional convenience that never
    affects equality (blocks compare order-insensitively).
    """

    type_name = 'block'

    def __init__(self, *args, **kwargs):
        from .serialization import from_plain
        dict.__init__(self)
        for key, value in dict(*args, **kwargs).items():
            dict.__setitem__(self, key, from_plain(value))

    def __setitem__(self, key, value):
        from .serialization import from_plain
        dict.__setitem__(self, key, from_plain(value))

    def as_text(self):
        return str(self)

    def to_serialized(self):
        return {
            'type': 'block',
            'value': {key: child.to_serialized() for key, child in self.items()},
        }

    # -- field access -------------------------------------------------------

    def field(self, name):
        """Return the field named ``name`` (raise ``ValueError`` if missing)."""
        if name not in self:
            raise ValueError(f'field {name!r} not found in block')
        return self[name]

    def select_field(self, name):
        return self.field(name)

    def map_fields(self, func):
        """Return a block with the same field names and ``func(value)`` per field."""
        return Block({key: func(child) for key, child in self.items()})

    def count(self):
        return len(self)

    def length(self):
        raise TypeError('block: length is defined for text, got block')

    # -- positional convenience (unchanged from the dict-subclass design) -----

    def child_at(self, index):
        """Return the field value at ``index`` (0-based, insertion order)."""
        return list(self.values())[index]

    def field_name_at(self, index):
        """Return the field name at ``index`` (0-based, insertion order)."""
        return list(self.keys())[index]

    # -- generic children / tree walking ------------------------------------

    def child_keys(self):
        return list(self.keys())

    def has_child(self, key):
        return key in self

    def child(self, key):
        return self[key]

    def children(self):
        yield from self.items()

    def iter_child_paths(self, index_prefix, name_prefix):
        for key, child in self.items():
            yield child, index_prefix + [key], name_prefix + [key]

    def iter_leaves(self):
        for child in self.values():
            yield from child.iter_leaves()

    def iter_leaves_with_paths(self, prefix=()):
        for key, child in self.items():
            yield from child.iter_leaves_with_paths(list(prefix) + [key])

    def _map_leaves(self, func, path):
        return Block({
            key: child._map_leaves(func, path + [key])
            for key, child in self.items()
        })


class Collection(Compound, list):
    """A collection: an ordered sequence of elements addressable both by
    zero-based index and by a unique element name.

    The runtime spelling is a ``list`` subclass, so ``isinstance(value, list)``
    keeps working. On top of the list items it carries the per-element names
    (``names``) and a ``name -> index`` lookup (``by_name``).

    - index access: ``coll[i]`` — 0-based, negative counts from the end.
    - name access: ``coll.index_of(name)`` / ``coll.get(name)`` / ``coll.by_name``.
    - equality is order-sensitive by default (inherited from ``list``).
    """

    type_name = 'collection'

    def __init__(self, items=(), names=None):
        from .serialization import from_plain
        items = [from_plain(item) for item in items]
        super().__init__(items)
        if names is None:
            names = [str(index + 1) for index in range(len(items))]
        names = list(names)
        if len(names) != len(items):
            raise ValueError(
                f'Collection: {len(items)} items but {len(names)} names'
            )
        self.names = names
        self.by_name = {}
        for index, name in enumerate(names):
            if name in self.by_name:
                raise ValueError(
                    f'Collection: duplicate element name {name!r}'
                )
            self.by_name[name] = index

    def __setitem__(self, index, value):
        from .serialization import from_plain
        list.__setitem__(self, index, from_plain(value))

    def append(self, value):
        from .serialization import from_plain
        list.append(self, from_plain(value))

    def insert(self, index, value):
        from .serialization import from_plain
        list.insert(self, index, from_plain(value))

    def extend(self, values):
        from .serialization import from_plain
        list.extend(self, (from_plain(value) for value in values))


    def as_text(self):
        return str(self)

    def to_serialized(self):
        return {
            'type': 'collection',
            'value': [child.to_serialized() for child in self],
        }

    # -- element access -----------------------------------------------------

    def name_at(self, index):
        return self.names[index]

    def index_of(self, name):
        return self.by_name[name]

    def get(self, name, default=None):
        index = self.by_name.get(name)
        if index is None:
            return default
        return self[index]

    def item(self, index):
        """Return the element at ``index`` (0-based; negative counts from the end)."""
        if isinstance(index, bool) or not isinstance(index, int):
            raise TypeError(
                f'collection index must be an integer, got {type(index).__name__}'
            )
        try:
            return self[index]
        except IndexError:
            raise ValueError(
                f'index {index} out of range for collection of length {len(self)}'
            ) from None

    def item_by_name(self, name):
        return self[self.by_name[name]]

    def select_field(self, name):
        return self.project(name)

    def project(self, name):
        """Return a collection of ``item.select_field(name)`` per element."""
        return Collection(
            [item.select_field(name) for item in self],
            self.names,
        )

    def slice(self, start=None, stop=None):
        """Return ``self[start:stop]`` (Python slice semantics, names preserved)."""
        start = _slice_index(start, 'start')
        stop = _slice_index(stop, 'stop')
        return Collection(self[start:stop], self.names[start:stop])

    def map(self, func):
        return Collection([func(item) for item in self], self.names)

    def filter(self, func):
        kept = []
        kept_names = []
        for index, item in enumerate(self):
            if func(item):
                kept.append(item)
                if self.names is not None:
                    kept_names.append(self.names[index])
        return Collection(kept, kept_names if self.names is not None else None)

    def sort(self, by=None, descending=False):
        """Sort the collection (optionally by a block field)."""
        def key_for(index):
            return self[index][by] if by is not None else self[index]

        try:
            order = sorted(range(len(self)), key=key_for)
        except TypeError as error:
            if by is None:
                raise TypeError(
                    'sort: cannot sort a collection of blocks without a `by` field'
                ) from error
            raise

        if descending:
            order.reverse()

        result = [self[index] for index in order]
        names = [self.names[index] for index in order] if self.names is not None else None
        return Collection(result, names)

    def count(self):
        return len(self)

    def length(self):
        raise TypeError('collection: length is defined for text, got collection')

    # -- generic children / tree walking ------------------------------------

    def child_keys(self):
        return list(range(len(self)))

    def has_child(self, key):
        if isinstance(key, int) and not isinstance(key, bool):
            return -len(self) <= key < len(self)
        return key in self.by_name

    def child(self, key):
        if isinstance(key, str):
            return self.item_by_name(key)
        return self.item(key)

    def children(self):
        for index, child in enumerate(self):
            yield index, self.name_at(index), child

    def iter_child_paths(self, index_prefix, name_prefix):
        for index, child in enumerate(self):
            child_index = index_prefix + [index]
            name = self.name_at(index)
            child_name = name_prefix + [name] if name is not None else child_index
            yield child, child_index, child_name

    def iter_leaves(self):
        for child in self:
            yield from child.iter_leaves()

    def iter_leaves_with_paths(self, prefix=()):
        for index, child in enumerate(self):
            yield from child.iter_leaves_with_paths(list(prefix) + [index])

    def _map_leaves(self, func, path):
        return Collection(
            [child._map_leaves(func, path + [index]) for index, child in enumerate(self)],
            self.names,
        )


def _slice_index(value, name):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(
            f'collection slice: {name} must be an integer or omitted, got '
            f'{type(value).__name__}'
        )
    return value



"""Python spelling of the cmdlet value taxonomy.

See `docs/cmdlet-data-formats.md` for the authoritative description. A cmdlet
produces and receives exactly one value per pipe step; that value is one of the
scalar or compound types below, or ``sysmissing`` (Python ``None``).

Runtime representation stays plain Python: ``str``/``int``/``float``/``bool``/
``datetime.date``/``datetime.datetime``/``pathlib.Path`` for scalars, ``Block``
(a ``dict`` subclass) for a block, and ``Collection`` (a ``list`` subclass
carrying per-element names) for a collection; ``None`` is sysmissing.

The class hierarchy is::

    Value (ABC)
    ├── Scalar (ABC)             a scalar leaf — plain Python at runtime
    │   ├── CategoricalSingle    (marker, future value object)
    │   └── CategoricalMulti     (marker, future value object)
    ├── Compound (ABC)
    │   ├── Block(dict)          a block of named fields
    │   └── Collection(list)     an ordered, named + indexed collection
    └── sysmissing               ``None``

The scalar category names (``Text``, ``Integer``, …) are aliases to the plain
Python forms; ``Block`` and ``Collection`` are real runtime classes so producers
can emit them and consumers can check them with ``isinstance``.
"""

from abc import ABC
from datetime import date, datetime
from pathlib import Path
from typing import Optional, Union

__all__ = [
    'Value',
    'PipeValue',
    'Scalar',
    'Compound',
    'Text',
    'Integer',
    'Real',
    'Boolean',
    'PathValue',
    'DateTime',
    'CategoricalSingle',
    'CategoricalMulti',
    'Block',
    'Collection',
    'from_plain',
]


class Value(ABC):
    """Root base type: anything a cmdlet can produce or receive in a pipe."""


class Scalar(Value, ABC):
    """A scalar value (a leaf). Runtime spelling is plain Python."""


class Compound(Value, ABC):
    """A compound value: a block or a collection."""


# Scalar categories. Each is the plain Python type it uses at runtime.
Text = str
Integer = int
Real = float
Boolean = bool
PathValue = Path
DateTime = Union[date, datetime]


class CategoricalSingle(Scalar):
    """A single-punch categorical (future: a value object carrying options)."""


class CategoricalMulti(Scalar):
    """A multi-punch categorical (future: a value object carrying options)."""


class Block(Compound, dict):
    """A block: the named fields of an object (a ``dict`` subclass).

    Fields are addressed by name (``block['field']``). Because a ``dict``
    preserves insertion order, a field can also be read by its 0-based position
    via :meth:`child_at` — a positional convenience that never affects equality
    (blocks compare order-insensitively).
    """

    def child_at(self, index):
        """Return the field value at ``index`` (0-based, insertion order)."""
        return list(self.values())[index]

    def field_name_at(self, index):
        """Return the field name at ``index`` (0-based, insertion order)."""
        return list(self.keys())[index]

    def children(self):
        """Yield ``(field_name, field_value)`` pairs in insertion order."""
        yield from self.items()


class Collection(Compound, list):
    """A collection: an ordered sequence of elements addressable both by
    zero-based index and by a unique name.

    The runtime spelling is a ``list`` subclass, so any consumer that tests
    ``isinstance(value, list)`` keeps working unchanged. On top of the list
    items it carries the per-element names (``names``) and a ``name -> index``
    lookup (``by_name``), materialized by the producer.

    - index access: ``coll[i]`` — 0-based, negative counts from the end (plain
      ``list`` behaviour).
    - name access: ``coll.index_of(name)`` / ``coll.get(name)`` /
      ``coll.by_name[name]`` — names are unique within the collection.
    - equality is order-sensitive by default (inherited from ``list``); a
      comparison op opts out via its ``unordered_arrays`` argument.
    """

    def __init__(self, items=(), names=None):
        items = list(items)
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

    def name_at(self, index):
        """Return the element name at ``index`` (0-based)."""
        return self.names[index]

    def index_of(self, name):
        """Return the 0-based index of the element named ``name``."""
        return self.by_name[name]

    def get(self, name, default=None):
        """Return the element named ``name``, or ``default`` if absent."""
        index = self.by_name.get(name)
        if index is None:
            return default
        return self[index]

    def children(self):
        """Yield ``(index, element)`` pairs in order."""
        for index, element in enumerate(self):
            yield index, element


def from_plain(value):
    """Coerce plain-Python data (e.g. ``json.loads`` output) into the runtime
    taxonomy: every ``list`` becomes a ``Collection`` (with 1-based provisional
    names), ``dict`` stays a block with its values recursed, scalars pass through.

    An existing ``Collection`` keeps its names while its items are recursed, so
    the function is idempotent and never invents names for a value that already
    carries them.
    """
    if isinstance(value, Collection):
        return Collection([from_plain(item) for item in value], value.names)
    if isinstance(value, list):
        return Collection([from_plain(item) for item in value])
    if isinstance(value, dict):
        return Block({key: from_plain(child) for key, child in value.items()})
    return value


# A value or sysmissing (None) — what actually flows through a pipe step.
PipeValue = Optional[Value]

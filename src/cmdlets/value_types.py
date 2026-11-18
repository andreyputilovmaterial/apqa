"""Python spelling of the cmdlet value taxonomy.

See `docs/cmdlet-data-formats.md` for the authoritative description. A cmdlet
produces and receives exactly one value per pipe step; that value is one of the
scalar or compound types below, or ``sysmissing`` (Python ``None``).

Runtime representation stays plain Python: ``str``/``int``/``float``/``bool``/
``datetime.date``/``datetime.datetime``/``pathlib.Path`` for scalars, ``dict``
for a block, and ``Collection`` (a ``list`` subclass carrying per-element names)
for a collection; ``None`` is sysmissing. ``Block`` is a structural
``typing.Protocol`` and the scalar names are aliases to the plain Python forms,
used for type annotations and as living documentation; ``Collection`` is a real
runtime type (a ``list``) so producers can emit it and consumers can check it
with ``isinstance``.
"""

from datetime import date, datetime
from pathlib import Path
from typing import Iterator, Optional, Protocol, Union

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


class Value(Protocol):
    """Root base type: anything a cmdlet can produce or receive in a pipe."""


class Scalar(Value, Protocol):
    """A scalar value."""


class Compound(Value, Protocol):
    """A compound value: a block or a collection."""


# Scalar categories. Each is the plain Python type it uses at runtime.
Text = str
Integer = int
Real = float
Boolean = bool
PathValue = Path
DateTime = Union[date, datetime]


class CategoricalSingle(Scalar, Protocol):
    """A single-punch categorical (future: a value object carrying options)."""


class CategoricalMulti(Scalar, Protocol):
    """A multi-punch categorical (future: a value object carrying options)."""


class Block(Compound, Protocol):
    """A block: a mapping of named fields to values (Python ``dict``)."""

    def __getitem__(self, key: str) -> Value: ...
    def __iter__(self) -> Iterator[str]: ...
    def __len__(self) -> int: ...


class Collection(list):
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
        return {key: from_plain(child) for key, child in value.items()}
    return value


# A value or sysmissing (None) — what actually flows through a pipe step.
PipeValue = Optional[Value]

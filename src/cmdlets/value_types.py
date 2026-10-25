"""Python spelling of the cmdlet value taxonomy.

See `docs/cmdlet-data-formats.md` for the authoritative description. A cmdlet
produces and receives exactly one value per pipe step; that value is one of the
scalar or compound types below, or ``sysmissing`` (Python ``None``).

Runtime representation stays plain Python: ``str``/``int``/``float``/``bool``/
``datetime.date``/``datetime.datetime``/``pathlib.Path`` for scalars, ``dict``
for a block, ``list`` for an array, and ``None`` for sysmissing. The names here
are structural ``typing.Protocol`` types (for the compound shapes) and aliases to
the plain scalar forms, used for type annotations and as living documentation —
they do **not** wrap values at runtime.
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
    'NamedCollection',
    'Array',
]


class Value(Protocol):
    """Root base type: anything a cmdlet can produce or receive in a pipe."""


class Scalar(Value, Protocol):
    """A scalar value."""


class Compound(Value, Protocol):
    """A compound value: a block, a named collection, or an array."""


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


class NamedCollection(Block, Protocol):
    """A block with a fixed field order (provisional)."""


class Array(Compound, Protocol):
    """An array: a sequence of values (Python ``list``)."""

    def __getitem__(self, index: int) -> Value: ...
    def __iter__(self) -> Iterator[Value]: ...
    def __len__(self) -> int: ...


# A value or sysmissing (None) — what actually flows through a pipe step.
PipeValue = Optional[Value]

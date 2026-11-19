"""The cmdlet value taxonomy.

A single, self-contained library of the types that flow through a cmdlet pipe.
Every value is an instance of :class:`Value` (or one of its subclasses) — never a
raw Python primitive. See ``docs/cmdlet-data-formats.md`` for the authoritative
description.
"""

from .base import (
    Value,
    Scalar,
    Compound,
    SysMissing,
    sysmissing,
    is_sysmissing,
    PipeValue,
)
from .scalars import (
    Text,
    Integer,
    Real,
    Boolean,
    PathValue,
    DateTime,
    CategoricalSingle,
    CategoricalMulti,
)
from .compound import Block, Collection
from .serialization import (
    from_plain,
    from_serialized,
    to_serialized,
    coerce,
    format_path,
)

__all__ = [
    'Value',
    'Scalar',
    'Compound',
    'SysMissing',
    'sysmissing',
    'is_sysmissing',
    'PipeValue',
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
    'from_serialized',
    'to_serialized',
    'coerce',
    'format_path',
]

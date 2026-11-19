"""Serialization and path rendering for the cmdlet value taxonomy.

``from_plain`` turns raw Python/JSON data (``json.loads`` output, source-reader
results) into ``Value`` instances — the one place raw data enters the taxonomy.
``from_serialized`` / ``to_serialized`` are the *typed* round-trip used when a
literal value is stored inside a QC rule (``{'type': ..., 'value': ...}``, or
``{'type': 'sysmissing'}``). ``format_path`` renders a data path (the sequence of
block keys and collection indices leading to a leaf) into its human-readable
address, used by diagnostics and the ``exclude-*``/``include-*`` rules.
"""

import re
from datetime import date, datetime
from pathlib import Path

from .base import Value, sysmissing
from .compound import Block, Collection
from .scalars import Boolean, DateTime, Integer, PathValue, Real, Text

__all__ = [
    'from_plain',
    'from_serialized',
    'to_serialized',
    'coerce',
    'format_path',
]

_IDENTIFIER = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')


def from_plain(value):
    """Wrap raw Python/JSON data into the value taxonomy.

    ``None`` -> ``sysmissing``, ``bool`` -> ``Boolean``, ``int`` -> ``Integer``,
    ``float`` -> ``Real``, ``str`` -> ``Text``, ``date``/``datetime`` ->
    ``DateTime``, ``Path`` -> ``PathValue``, ``list`` -> ``Collection`` (1-based
    provisional names), ``dict`` -> ``Block``. An existing ``Value`` is returned
    as-is — ``Block``/``Collection`` auto-wrap their own children on
    construction, so a ``Value`` is always fully wrapped.
    """
    if isinstance(value, Value):
        return value
    if value is None:
        return sysmissing
    if isinstance(value, bool):
        return Boolean(value)
    if isinstance(value, int):
        return Integer(value)
    if isinstance(value, float):
        return Real(value)
    if isinstance(value, str):
        return Text(value)
    if isinstance(value, datetime):
        return DateTime(value)
    if isinstance(value, date):
        return DateTime(value)
    if isinstance(value, Path):
        return PathValue(value)
    if isinstance(value, list):
        return Collection([from_plain(item) for item in value])
    if isinstance(value, dict):
        return Block({key: from_plain(child) for key, child in value.items()})
    return value


def from_serialized(data):
    """Build a ``Value`` from its typed serialized form.

    Accepts either a typed wrapper (``{'type': ..., 'value': ...}`` or
    ``{'type': 'sysmissing'}``) or a bare JSON value (which is normalized via
    :func:`from_plain`, so rules stored before the typed form keep working).
    """
    if isinstance(data, dict) and 'type' in data and (
        data['type'] == 'sysmissing' or 'value' in data
    ):
        return _from_typed(data)
    return from_plain(data)


def _from_typed(data):
    type_name = data['type']
    value = data.get('value')
    if type_name == 'sysmissing':
        return sysmissing
    if type_name == 'text':
        return Text(value)
    if type_name == 'integer':
        return Integer(int(value))
    if type_name == 'real':
        return Real(float(value))
    if type_name == 'number':
        return Integer(int(value)) if _is_int(value) else Real(float(value))
    if type_name == 'boolean':
        return Boolean(bool(value))
    if type_name == 'path':
        return PathValue(Path(value))
    if type_name == 'date':
        return DateTime(_parse_datetime(value))
    if type_name == 'block':
        return Block({key: from_serialized(child) for key, child in value.items()})
    if type_name == 'collection':
        return Collection([from_serialized(item) for item in value])
    raise ValueError(f'unknown serialized value type {type_name!r}')


def to_serialized(value):
    """Return the typed serialized form of ``value`` (normalizing raw input)."""
    return coerce(value).to_serialized()


def coerce(value):
    """Return ``value`` as a ``Value`` — raw data is wrapped, ``Value`` passes through."""
    return value if isinstance(value, Value) else from_plain(value)


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _parse_datetime(text):
    text = str(text)
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return date.fromisoformat(text)


def format_path(path):
    """Render a data path as a short, human-readable address.

    ``['Fields', 'BrandAwareness', 'Label']`` becomes
    ``Fields.BrandAwareness.Label``; collection indices become ``[i]``; a key
    that is not a plain identifier is quoted, e.g.
    ``Fields.Gender.Elements['None of the above'].Label``.
    """
    result = ''
    for part in path:
        if isinstance(part, int):
            result += f'[{part}]'
            continue
        text = f'{part}'
        if _IDENTIFIER.match(text):
            if result:
                result += '.'
            result += text
        else:
            result += f'[{text!r}]'
    return result

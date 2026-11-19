"""Concrete scalar value classes."""

from datetime import date, datetime
from pathlib import Path

from .base import Scalar

__all__ = [
    'Text',
    'Integer',
    'Real',
    'Boolean',
    'PathValue',
    'DateTime',
    'CategoricalSingle',
    'CategoricalMulti',
]


class Text(Scalar):
    """A text value (wraps a ``str``)."""

    type_name = 'text'

    def __contains__(self, item):
        needle = item.value if isinstance(item, Text) else item
        return needle in self.value

    def count(self):
        return 0 if self.value == '' else 1

    def length(self):
        return len(self.value)


class Integer(Scalar):
    """An integer value (wraps an ``int``)."""

    type_name = 'integer'


class Real(Scalar):
    """A floating-point value (wraps a ``float``)."""

    type_name = 'real'


class Boolean(Scalar):
    """A boolean value (wraps a ``bool``)."""

    type_name = 'boolean'


class PathValue(Scalar):
    """A filesystem-path value (wraps a ``pathlib.Path``)."""

    type_name = 'path'

    def _serialize_value(self):
        return str(self.value)


class DateTime(Scalar):
    """A date/time value (wraps a ``datetime.date`` or ``datetime.datetime``).

    Per the dates & time rules, datetimes are timezone-aware (UTC in storage).
    """

    type_name = 'date'

    def _serialize_value(self):
        return self.value.isoformat()


class CategoricalSingle(Scalar):
    """A single-punch categorical value (carries its options in the future)."""

    type_name = 'categorical-single'


class CategoricalMulti(Scalar):
    """A multi-punch categorical value (carries its punches in the future)."""

    type_name = 'categorical-multi'

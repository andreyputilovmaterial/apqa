"""The ``sysmissing`` value (re-exported from the value taxonomy).

``sysmissing`` is a singleton :class:`SysMissing` instance — the first-class
value a cmdlet produces/receives when a value is missing (like SQL ``NULL``). It
is deliberately distinct from every *empty* value (``''``, ``{}``, ``[]``, ``0``,
``False``) and from Python ``None``.
"""

from .value_types import SysMissing, sysmissing, is_sysmissing

__all__ = ['SysMissing', 'sysmissing', 'is_sysmissing']


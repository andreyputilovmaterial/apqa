"""Base classes of the cmdlet value taxonomy.

Every value that flows through a cmdlet pipe is an instance of a class derived
from :class:`Value` — never a raw Python primitive. The hierarchy is::

    Value (ABC)
    ├── SysMissing            the missing value (a singleton instance ``sysmissing``)
    ├── Scalar (ABC)          a scalar leaf wrapping a raw Python value
    │   ├── Text / Integer / Real / Boolean / PathValue / DateTime
    │   └── CategoricalSingle / CategoricalMulti
    └── Compound (ABC)
        ├── Block(dict)       a block of named fields
        └── Collection(list)  an ordered, named + indexed collection

Scalars store their raw payload in the ``.value`` attribute (the *straightforward*
way to reach the underlying text / number / boolean / path / date). Compounds are
``dict``/``list`` subclasses whose own children are ``Value`` instances, so a
block/collection is itself a ``Value`` as well.
"""

from abc import ABC, abstractmethod

__all__ = [
    'Value',
    'Scalar',
    'Compound',
    'SysMissing',
    'sysmissing',
    'is_sysmissing',
    'PipeValue',
]


class Value(ABC):
    """Root base type: anything a cmdlet can produce or receive in a pipe."""

    #: The stable type name used in serialized form (``'text'``, ``'integer'``,
    #: ``'block'``, ``'sysmissing'``, ...). Overridden by every concrete class.
    type_name = 'value'

    @property
    def value(self):
        """The raw Python payload.

        Scalars return the wrapped primitive (``str``/``int``/``float``/``bool``/
        ``Path``/``date``/``datetime``); compounds return ``self``; sysmissing
        returns ``None``.
        """
        return self

    @abstractmethod
    def as_text(self) -> str:
        """Return a plain-text rendering of this value."""

    @abstractmethod
    def to_serialized(self):
        """Return the JSON-safe typed form ``{'type': ..., 'value': ...}``."""

    # -- sysmissing ---------------------------------------------------------

    def is_sysmissing(self):
        return False

    def count(self):
        """Number of meaningful entries (``1`` for a stored scalar leaf)."""
        return 1

    def length(self):
        """Number of characters (text only)."""
        raise TypeError(f'{self.type_name}: length is defined for text, got {self.type_name}')

    # -- child access (compound types override) -----------------------------

    def child_keys(self):
        """Return the ordered addresses of the direct children (empty for leaves)."""
        return []

    def has_child(self, key):
        return False

    def child(self, key):
        """Return the direct child at ``key`` (field name / index / element name)."""
        raise TypeError(f'{self.type_name}: has no children')

    # -- shape operations (compound types override; leaves raise) ------------

    def select_field(self, name, missing_ok=False):
        raise TypeError(f'{self.type_name}: cannot select a field')

    def item(self, index, missing_ok=False):
        raise TypeError(f'{self.type_name}: cannot select an item')

    def slice(self, start=None, stop=None):
        raise TypeError(f'{self.type_name}: cannot slice')

    def map(self, func):
        raise TypeError(f'{self.type_name}: cannot map over items')

    def map_fields(self, func):
        raise TypeError(f'{self.type_name}: cannot map over fields')

    def filter(self, func):
        raise TypeError(f'{self.type_name}: cannot filter')

    def sort(self, by=None, descending=False):
        raise TypeError(f'{self.type_name}: cannot sort')


    def children(self):
        """Yield the direct children (blocks yield ``(name, child)``, collections
        yield ``(index, name, child)``, leaves yield nothing)."""
        return iter(())

    def iter_child_paths(self, index_prefix, name_prefix):
        """Yield ``(child, index_path, name_path)`` for each direct child."""
        return iter(())

    # -- tree walking (compound types override) -----------------------------

    def iter_leaves(self):
        """Yield every scalar leaf of this value, depth-first."""
        yield self

    def iter_leaves_with_paths(self, prefix=()):
        """Yield ``(leaf, path)`` for every scalar leaf, depth-first."""
        yield self, list(prefix)

    def map_leaves(self, func):
        """Return a new value where ``func(leaf, path)`` replaces each scalar leaf."""
        return self._map_leaves(func, [])

    def _map_leaves(self, func, path):
        return func(self, path)


class Scalar(Value, ABC):
    """A scalar leaf: wraps a raw Python value in ``.value``.

    Scalars compare equal to another scalar of the same *kind* with the same
    value, and to the raw Python value they wrap (a convenience so callers and
    tests can read ``Integer(42) == 42``). ``Boolean`` is deliberately distinct
    from ``Integer``/``Real`` (a ``True`` never equals ``1``).
    """

    def __init__(self, value):
        self._value = value

    @property
    def value(self):
        return self._value

    def as_text(self):
        return str(self.value)

    def to_serialized(self):
        return {'type': self.type_name, 'value': self._serialize_value()}

    def _serialize_value(self):
        return self.value

    # -- comparisons (natural order, used by ``sort`` and plain ``==``) -------

    def __eq__(self, other):
        if isinstance(other, Scalar):
            if (self.type_name == 'boolean') != (other.type_name == 'boolean'):
                return False
            return self.value == other.value
        return self.value == other

    def __hash__(self):
        return hash(self.value)

    def __bool__(self):
        return bool(self.value)

    def __lt__(self, other):
        if isinstance(other, Scalar):
            try:
                return self.value < other.value
            except TypeError:
                return NotImplemented
        return NotImplemented

    def __le__(self, other):
        if isinstance(other, Scalar):
            try:
                return self.value <= other.value
            except TypeError:
                return NotImplemented
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, Scalar):
            try:
                return self.value > other.value
            except TypeError:
                return NotImplemented
        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, Scalar):
            try:
                return self.value >= other.value
            except TypeError:
                return NotImplemented
        return NotImplemented

    def __repr__(self):
        return f'{type(self).__name__}({self.value!r})'


class Compound(Value, ABC):
    """A compound value: a block or a collection."""

    @property
    def value(self):
        return self


class SysMissing(Value):
    """The ``sysmissing`` value: a value is missing (like SQL ``NULL``).

    ``sysmissing`` is a singleton instance of this class. It is deliberately
    distinct from every *empty* value (``''``, ``{}``, ``[]``, ``0``, ``False``)
    and from Python ``None`` — it is a first-class ``Value`` that flows through
    the pipe like any other.
    """

    type_name = 'sysmissing'

    def __init__(self):
        pass

    @property
    def value(self):
        return None

    def is_sysmissing(self):
        return True

    def count(self):
        return 0

    def as_text(self):
        return ''

    def to_serialized(self):
        return {'type': 'sysmissing'}

    def __eq__(self, other):
        return isinstance(other, SysMissing) or other is None

    def __hash__(self):
        return hash(None)

    def __bool__(self):
        return False

    def __repr__(self):
        return 'sysmissing'


#: The single ``sysmissing`` instance — what actually flows through the pipe.
sysmissing = SysMissing()


def is_sysmissing(value):
    """Return ``True`` when ``value`` is the ``sysmissing`` value.

    ``None`` is also accepted for convenience (raw data is normalized into the
    value taxonomy by :func:`from_plain`).
    """
    return isinstance(value, SysMissing) or value is None


#: A value flowing through a pipe step — always a :class:`Value`, including
#: ``sysmissing``.
PipeValue = Value


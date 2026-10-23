
class _SysMissing:
    """Singleton sentinel for the ``sysmissing`` value.

    ``sysmissing`` is distinct from ``None``, ``0``, ``False``, and the empty
    string/collection: it marks a value that is *missing* (like SQL ``NULL``),
    and it is an allowed value for every scalar type.
    """

    def __repr__(self):
        return 'sysmissing'


sysmissing = _SysMissing()


def is_sysmissing(value):
    return value is sysmissing


"""The ``sysmissing`` value.

``sysmissing`` is represented as Python ``None``, mirroring how SQL ``NULL`` and
JSON ``null`` become ``None`` when read into Python.

``None``/``sysmissing`` is deliberately distinct from *empty* values: an empty
array, an empty block, a nothing-punched multi-punch, an empty string, zero, and
``False`` are all real values, whereas ``None`` means the value is missing.
"""

sysmissing = None


def is_sysmissing(value):
    return value is None

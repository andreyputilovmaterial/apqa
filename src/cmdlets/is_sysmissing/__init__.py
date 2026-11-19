"""`is-sysmissing` — is the incoming value ``sysmissing``?"""

from ..registry import cmdlets
from ..value_types import Boolean, PipeValue, coerce
from ..value_types import is_sysmissing as _is_sysmissing


@cmdlets.register('is-sysmissing', kind='terminal')
def is_sysmissing(value: PipeValue, args: dict) -> Boolean:
    """Return ``True`` when the value is ``sysmissing``.

    Only ``sysmissing`` itself counts: empty values (``""``, ``{}``, ``[]``,
    ``0``, ``False``) are real values, and a compound whose fields/items are all
    ``sysmissing`` is still a real value — so neither is reported as sysmissing.
    """
    return Boolean(_is_sysmissing(coerce(value)))


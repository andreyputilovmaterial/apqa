"""`is-sysmissing` — is the incoming value ``sysmissing``?"""

from ..registry import cmdlets
from ..value_types import PipeValue


@cmdlets.register('is-sysmissing')
def is_sysmissing(value: PipeValue, args: dict) -> bool:
    """Return ``True`` when the value is ``sysmissing`` (Python ``None``).

    Only ``sysmissing`` itself counts: empty values (``""``, ``{}``, ``[]``,
    ``0``, ``False``) are real values, and a compound (block/array) whose
    fields/items are all ``sysmissing`` is still a real value — so neither is
    reported as sysmissing.
    """
    return value is None

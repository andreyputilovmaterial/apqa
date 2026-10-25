"""`count` — count the meaningful entries in the incoming value."""

from ..registry import cmdlets
from ..sysmissing import is_sysmissing
from ..value_types import PipeValue


@cmdlets.register('count')
def count(value: PipeValue, args: dict) -> int:
    """Count the meaningful entries in the incoming value.

    - array (``list``): number of iterations.
    - block / named collection (``dict``): number of fields.
    - multi-punch categorical: number of punched categories (today a punch list
      is a plain ``list`` and counts as its length, like an array).
    - single-punch categorical, text, or any other scalar: ``1`` if a value is
      stored (i.e. it is not ``sysmissing``). Text is one stored value and is
      not counted character-by-character.
    - ``sysmissing`` (``None``): ``0`` by default; ``args['fail_on_sysmissing']``
      raises instead.
    """
    if is_sysmissing(value):
        if bool(args.get('fail_on_sysmissing', False)):
            raise ValueError('count: cannot count a sysmissing value')
        return 0

    if isinstance(value, str):
        return 1
    if isinstance(value, dict):
        return len(value)
    if isinstance(value, list):
        return len(value)
    return 1

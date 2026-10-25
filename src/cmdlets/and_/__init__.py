"""`and` — logical AND over operand cmdlet chains."""

from ..operands import eval_operand_chains
from ..registry import cmdlets
from ..value_types import Boolean, PipeValue


@cmdlets.register('and')
def and_(value: PipeValue, args: dict) -> Boolean:
    """Return ``True`` iff every operand chain's value is truthy.

    Each operand is a cmdlet chain in ``args['operands']`` (each chain starts
    with a source reader); every operand is converted to boolean, so
    ``sysmissing`` counts as ``False``. The piped value is ignored.
    """
    return all(bool(result) for result in eval_operand_chains(args, 'and'))

"""`bit-lshift` — bitwise left shift over integer operand chains."""

from functools import reduce
import operator

from ..operands import eval_operand_chains, require_int
from ..registry import cmdlets
from ..value_types import Integer, PipeValue


@cmdlets.register('bit-lshift')
def bit_lshift(value: PipeValue, args: dict) -> Integer:
    """Return the integer operands left-shifted left-to-right (``a << b``).

    Each operand is a cmdlet chain in ``args['operands']``; every result must be
    an integer (bool excluded). The piped value is ignored.
    """
    results = [
        require_int(result, 'bit-lshift')
        for result in eval_operand_chains(args, 'bit-lshift')
    ]
    return reduce(operator.lshift, results)

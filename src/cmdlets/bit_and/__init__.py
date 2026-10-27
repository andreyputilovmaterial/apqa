"""`bit-and` — bitwise AND over integer operand chains."""

from functools import reduce
import operator

from ..operands import eval_operand_chains, require_int
from ..registry import cmdlets
from ..value_types import Integer, PipeValue


@cmdlets.register(
    'bit-and',
    kind='source',
    args=[
        {
            'name': 'operands',
            'type': 'cmdlet-chains',
            'required': True,
            'description': 'Integer cmdlet chains combined with bitwise AND.',
        },
    ],
)
def bit_and(value: PipeValue, args: dict) -> Integer:
    """Return the bitwise AND of the integer operand chains.

    Each operand is a cmdlet chain in ``args['operands']``; every result must be
    an integer (bool excluded). The piped value is ignored.
    """
    results = [
        require_int(result, 'bit-and')
        for result in eval_operand_chains(args, 'bit-and')
    ]
    return reduce(operator.and_, results)

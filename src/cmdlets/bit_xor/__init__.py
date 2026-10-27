"""`bit-xor` — bitwise XOR over integer operand chains."""

from functools import reduce
import operator

from ..operands import eval_operand_chains, require_int
from ..registry import cmdlets
from ..value_types import Integer, PipeValue


@cmdlets.register(
    'bit-xor',
    kind='source',
    args=[
        {
            'name': 'operands',
            'type': 'cmdlet-chains',
            'required': True,
            'description': 'Integer cmdlet chains combined with bitwise XOR.',
        },
    ],
)
def bit_xor(value: PipeValue, args: dict) -> Integer:
    """Return the bitwise XOR of the integer operand chains.

    Each operand is a cmdlet chain in ``args['operands']``; every result must be
    an integer (bool excluded). The piped value is ignored.
    """
    results = [
        require_int(result, 'bit-xor')
        for result in eval_operand_chains(args, 'bit-xor')
    ]
    return reduce(operator.xor, results)

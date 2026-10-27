"""`bit-rshift` — bitwise right shift over integer operand chains."""

from functools import reduce
import operator

from ..operands import eval_operand_chains, require_int
from ..registry import cmdlets
from ..value_types import Integer, PipeValue


@cmdlets.register(
    'bit-rshift',
    kind='source',
    args=[
        {
            'name': 'operands',
            'type': 'cmdlet-chains',
            'required': True,
            'description': 'Integer cmdlet chains right-shifted left-to-right.',
        },
    ],
)
def bit_rshift(value: PipeValue, args: dict) -> Integer:
    """Return the integer operands right-shifted left-to-right (``a >> b``).

    Each operand is a cmdlet chain in ``args['operands']``; every result must be
    an integer (bool excluded). The piped value is ignored.
    """
    results = [
        require_int(result, 'bit-rshift')
        for result in eval_operand_chains(args, 'bit-rshift')
    ]
    return reduce(operator.rshift, results)

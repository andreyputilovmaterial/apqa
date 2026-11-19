"""`bitwise-lshift` — bitwise left shift over integer operand chains."""

from functools import reduce
import operator

from ..operands import eval_operand_chains, require_int
from ..registry import cmdlets
from ..value_types import Integer, PipeValue


@cmdlets.register(
    'bitwise-lshift',
    kind='source',
    args=[
        {
            'name': 'operands',
            'type': 'cmdlet-chains',
            'required': True,
            'description': 'Integer cmdlet chains left-shifted left-to-right.',
        },
    ],
    compact=[
        {'text': 'BITLSHIFT('},
        {'arg': 'operands', 'role': 'operands'},
        {'text': ')'},
    ],
)
def bitwise_lshift(value: PipeValue, args: dict) -> Integer:
    """Return the integer operands left-shifted left-to-right (``a << b``).

    Each operand is a cmdlet chain in ``args['operands']``; every result must be
    an integer (bool excluded). The piped value is ignored.
    """
    results = [
        require_int(result, 'bitwise-lshift')
        for result in eval_operand_chains(args, 'bitwise-lshift')
    ]
    return Integer(reduce(operator.lshift, results))


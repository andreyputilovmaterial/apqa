"""`bitwise-or` — bitwise OR over integer operand chains."""

from functools import reduce
import operator

from ..operands import eval_operand_chains, require_int
from ..registry import cmdlets
from ..value_types import Integer, PipeValue


@cmdlets.register(
    'bitwise-or',
    kind='source',
    args=[
        {
            'name': 'operands',
            'type': 'cmdlet-chains',
            'required': True,
            'description': 'Integer cmdlet chains combined with bitwise OR.',
        },
    ],
    compact=[
        {'text': 'BITOR('},
        {'arg': 'operands', 'role': 'operands'},
        {'text': ')'},
    ],
)
def bitwise_or(value: PipeValue, args: dict) -> Integer:
    """Return the bitwise OR of the integer operand chains.

    Each operand is a cmdlet chain in ``args['operands']``; every result must be
    an integer (bool excluded). The piped value is ignored.
    """
    results = [
        require_int(result, 'bitwise-or')
        for result in eval_operand_chains(args, 'bitwise-or')
    ]
    return Integer(reduce(operator.or_, results))


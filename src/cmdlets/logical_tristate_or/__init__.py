"""`logical-tristate-or` — SQL-style three-valued OR over operand chains."""

from ..operands import eval_operand_chains
from ..registry import cmdlets
from ..tristate import tristate_or
from ..value_types import Boolean, PipeValue, sysmissing


@cmdlets.register(
    'logical-tristate-or',
    kind='source',
    args=[
        {
            'name': 'operands',
            'type': 'cmdlet-chains',
            'required': True,
            'description': 'Cmdlet chains combined with three-valued logical OR.',
        },
    ],
    compact=[
        {'text': 'OR('},
        {'arg': 'operands', 'role': 'operands'},
        {'text': ')'},
    ],
)
def logical_tristate_or(value: PipeValue, args: dict) -> PipeValue:
    """Return the SQL-style three-valued OR over operand chain results.

    The result is ``True`` when any operand is truthy, ``sysmissing`` when none
    is truthy but at least one is ``sysmissing``, and ``False`` when every
    operand is falsy. The piped value is ignored.
    """
    result = tristate_or(eval_operand_chains(args, 'logical-tristate-or'))
    return sysmissing if result is None else Boolean(result)


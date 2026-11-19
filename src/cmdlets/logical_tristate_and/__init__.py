"""`logical-tristate-and` — SQL-style three-valued AND over operand chains."""

from ..operands import eval_operand_chains
from ..registry import cmdlets
from ..tristate import tristate_and
from ..value_types import Boolean, PipeValue, sysmissing


@cmdlets.register(
    'logical-tristate-and',
    kind='source',
    args=[
        {
            'name': 'operands',
            'type': 'cmdlet-chains',
            'required': True,
            'description': 'Cmdlet chains combined with three-valued logical AND.',
        },
    ],
    compact=[
        {'text': 'AND('},
        {'arg': 'operands', 'role': 'operands'},
        {'text': ')'},
    ],
)
def logical_tristate_and(value: PipeValue, args: dict) -> PipeValue:
    """Return the SQL-style three-valued AND over operand chain results.

    The result is ``False`` when any operand is falsy, ``sysmissing`` when none
    is falsy but at least one is ``sysmissing``, and ``True`` when every operand
    is truthy. The piped value is ignored.
    """
    result = tristate_and(eval_operand_chains(args, 'logical-tristate-and'))
    return sysmissing if result is None else Boolean(result)


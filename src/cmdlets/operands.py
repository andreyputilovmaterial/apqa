"""Shared helpers for cmdlets that combine other cmdlet chains as operands."""

from .chain_runner import run_chain
from .value_types import Integer, coerce


def eval_operand_chains(args, name):
    """Run each chain in ``args['operands']`` and return their results."""
    operands = args.get('operands')
    if not operands:
        raise ValueError(
            f"{name}: missing required arg 'operands' (a list of cmdlet chains)"
        )
    if not isinstance(operands, list):
        raise ValueError(f"{name}: 'operands' must be a list of cmdlet chains")
    return [run_chain(chain) for chain in operands]



def require_int(value, name):
    """Return ``value``'s raw integer, or raise (bool excluded)."""
    value = coerce(value)
    if not isinstance(value, Integer):
        raise TypeError(
            f'{name}: expected an integer, got {value.type_name}'
        )
    return value.value


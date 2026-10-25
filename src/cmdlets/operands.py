"""Shared helpers for cmdlets that combine other cmdlet chains as operands."""

from .chain_runner import run_chain


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
    """Return ``value`` if it is an integer (excluding ``bool``), else raise."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(
            f'{name}: expected an integer, got {type(value).__name__}'
        )
    return value

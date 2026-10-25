
from .cmdlets import comparisons
from .cmdlets.chain_runner import run_chain  # re-exported for compatibility


def run_rule(rule):
    """Run a single QC rule and return ``True``/``False``.

    ``rule`` is the full rule representation as a JSON object (a ``dict``) with
    ``left`` (list of cmdlets), ``op`` (comparison op name), ``op_args``
    (optional mapping passed to the comparison op), and ``right`` (list of
    cmdlets); ``name``/``meta`` are accepted but ignored. A ``Rule`` instance
    (or anything exposing ``to_dict()``) is also accepted.

    A *false comparison* returns ``False``. Any *error* (missing/unknown cmdlet
    or op, unreadable data, bad arguments, …) raises an exception.
    """
    if not isinstance(rule, dict):
        to_dict = getattr(rule, 'to_dict', None)
        if callable(to_dict):
            rule = to_dict()
        else:
            raise ValueError(
                f'rule must be a mapping, got {type(rule).__name__}'
            )

    left = rule.get('left') or []
    right = rule.get('right') or []
    op = rule.get('op') or ''
    op_args = rule.get('op_args') or {}

    if not isinstance(left, list):
        raise ValueError('rule: left must be a list of cmdlets')
    if not isinstance(right, list):
        raise ValueError('rule: right must be a list of cmdlets')
    op = f'{op}'
    if op == '':
        raise ValueError('rule: missing comparison op')
    if not isinstance(op_args, dict):
        raise ValueError('rule: op_args must be a mapping')

    left_value = run_chain(left)
    right_value = run_chain(right)

    return comparisons.get(op)(left_value, right_value, op_args)


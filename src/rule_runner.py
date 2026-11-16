
from .cmdlets import comparisons
from .cmdlets.chain_runner import run_chain  # re-exported for compatibility
from .cmdlets.diagnostic import collect_notes


def run_rule(rule, settings=None):
    """Run a single QC rule and return ``True``/``False``.

    Convenience wrapper around :func:`run_rule_with_report` that discards the
    collected diagnostic notes. ``settings`` is the session's ``UserSettings``
    permission allow-list (``None`` grants every group).
    """
    result, _notes = run_rule_with_report(rule, settings=settings)
    return result


def run_rule_with_report(rule, settings=None):
    """Run a single QC rule and return ``(result, notes)``.

    ``rule`` is the full rule representation as a JSON object (a ``dict``) with
    ``left`` (list of cmdlets), ``op`` (comparison op name), ``op_args``
    (optional mapping passed to the comparison op), and ``right`` (list of
    cmdlets); ``name``/``meta`` are accepted but ignored. A ``Rule`` instance
    (or anything exposing ``to_dict()``) is also accepted.

    ``settings`` is the session's ``UserSettings`` permission allow-list (see
    ``src/user_settings.py``) used to gate each cmdlet; ``None`` grants every
    permission group, so all cmdlets run.

    ``result`` is ``True`` or ``False`` — a *false comparison* returns
    ``False``. ``notes`` is the list of diagnostic notes recorded by cmdlets
    that know *where* a value failed (see ``src/cmdlets/diagnostic.py`` and
    ``docs/qc-results-reporting.md``); it is empty when nothing recorded a note.

    Any *error* (missing/unknown cmdlet or op, unreadable data, bad arguments,
    a permission-denied cmdlet, …) raises; a cmdlet error is wrapped in
    ``ChainError`` identifying the step.
    """
    left, right, op, op_args = _parse_rule(rule)

    with collect_notes() as notes:
        left_value = run_chain(left, settings=settings)
        right_value = run_chain(right, settings=settings)
        result = comparisons.get(op)(left_value, right_value, op_args)

    return result, notes.items


def _parse_rule(rule):
    """Validate/normalize a rule into ``(left, right, op, op_args)``."""
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

    return left, right, op, op_args


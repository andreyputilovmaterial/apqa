"""Run a chain of cmdlets, threading each output into the next."""

from .registry import cmdlets
from ..user_settings import current_user_settings, user_settings_scope


class ChainError(Exception):
    """A cmdlet in a chain failed.

    Carries the failing step's position (``cmdlet``, ``step``, ``args``) and the
    original exception as ``__cause__``, so the full cause chain stays available
    to pytest and the HTTP endpoint (see ``docs/qc-results-reporting.md``).
    """

    def __init__(self, cmdlet, step, args, message):
        self.cmdlet = cmdlet
        self.step = step
        self.args = args
        super().__init__(message)


class PermissionDeniedError(Exception):
    """A cmdlet requires a permission group the session has not granted.

    Carries the cmdlet name and the sorted list of required groups. Raised from
    :func:`run_chain` before the cmdlet body executes, and wrapped in a
    ``ChainError`` (with this as ``__cause__``) so the failing step stays
    identifiable.
    """

    def __init__(self, cmdlet, required_groups):
        self.cmdlet = cmdlet
        self.required_groups = sorted(set(required_groups or ()))
        super().__init__(
            f'cmdlet {cmdlet!r} requires permission group(s): '
            f'{", ".join(self.required_groups)}'
        )


def run_chain(chain, initial=None, settings=None):
    """Run a chain of cmdlets, threading each output into the next.

    ``chain`` is a list of cmdlet mappings ``{'cmdlet': <name>, 'args': {...}}``.
    The first cmdlet receives ``initial`` (``None`` by default, since source
    readers take their input from their own ``args``).

    ``settings`` is the session's ``UserSettings`` allow-list (see
    ``src/user_settings.py``), or ``None`` to grant every permission group (the
    default). When omitted, the settings are inherited from the enclosing chain
    run, so nested chains (``map``'s transform, ``where``'s predicate, operand
    chains) are gated identically. A cmdlet whose declared permission groups
    are not granted by ``settings`` does not run: a ``PermissionDeniedError`` is
    raised and wrapped in a ``ChainError`` identifying the step.

    A failing cmdlet (including an unknown cmdlet name) raises `ChainError`
    identifying the step, with the original exception chained as ``__cause__``.
    """
    if settings is None:
        settings = current_user_settings()
    value = initial
    with user_settings_scope(settings):
        for index, step in enumerate(chain):
            if not isinstance(step, dict):
                raise ValueError(
                    f'cmdlet must be a mapping, got {type(step).__name__}'
                )
            name = step.get('cmdlet')
            if name is None or name == '':
                raise ValueError('cmdlet is missing a name')
            name = f'{name}'
            args = step.get('args') or {}
            if not isinstance(args, dict):
                raise ValueError(f"cmdlet {name!r}: args must be a mapping")
            try:
                _check_permissions(name, settings)
                value = cmdlets.get(name)(value, args)
            except ChainError:
                raise
            except Exception as error:
                raise ChainError(
                    cmdlet=name,
                    step=index,
                    args=args,
                    message=f'cmdlet {name!r} (step {index}): {error}',
                ) from error
    return value


def _check_permissions(name, settings):
    """Refuse to run ``name`` when its required groups are not granted."""
    if settings is None:
        return
    required = (cmdlets.describe(name) or {}).get('permissions') or []
    if not settings.is_permitted(required):
        raise PermissionDeniedError(name, required)

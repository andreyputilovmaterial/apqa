"""Run a chain of cmdlets, threading each output into the next."""

from .navigation import navigation_scope
from .registry import cmdlets


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


def run_chain(chain, initial=None):
    """Run a chain of cmdlets, threading each output into the next.

    ``chain`` is a list of cmdlet mappings ``{'cmdlet': <name>, 'args': {...}}``.
    The first cmdlet receives ``initial`` (``None`` by default, since source
    readers take their input from their own ``args``).

    A failing cmdlet (including an unknown cmdlet name) raises `ChainError`
    identifying the step, with the original exception chained as ``__cause__``.

    Each run also opens a fresh navigation-path scope (see
    ``src/cmdlets/navigation.py``) so navigating cmdlets can record their step
    and a downstream ``filter`` can read the path that led to its input.
    """
    value = initial
    with navigation_scope():
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

"""Run a chain of cmdlets, threading each output into the next."""

from .registry import cmdlets


def run_chain(chain, initial=None):
    """Run a chain of cmdlets, threading each output into the next.

    ``chain`` is a list of cmdlet mappings ``{'cmdlet': <name>, 'args': {...}}``.
    The first cmdlet receives ``initial`` (``None`` by default, since source
    readers take their input from their own ``args``).
    """
    value = initial
    for step in chain:
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
        value = cmdlets.get(name)(value, args)
    return value

"""In-memory user settings (not yet persisted).

The user settings are a placeholder: they live only in the process config for
one session and are never stored or saved anywhere. Right now they only carry
the permission-group allow-list used to gate cmdlet execution — each cmdlet
declares the permission groups it requires (see ``src/cmdlets/registry.py``)
and the chain runner refuses to run a cmdlet whose groups are not granted here
(see ``src/cmdlets/chain_runner.py``).

By default *all* permission groups are granted, so every cmdlet runs.
"""

from contextlib import contextmanager
from contextvars import ContextVar

__all__ = [
    'UserSettings',
    'user_settings_scope',
    'current_user_settings',
]


class UserSettings:
    """In-memory user settings for one session.

    Not persisted: an instance is created fresh by ``main_ui_program`` at the
    start of a session and discarded when the process exits. It currently only
    carries the permission-group allow-list used to gate cmdlet execution.

    ``permissions`` is a mapping of permission-group name to ``bool``. A group
    that is absent from the mapping is **granted by default**, so a fresh
    instance grants every group and every cmdlet runs. Set a group to ``False``
    to forbid the cmdlets that require it.
    """

    def __init__(self, permissions=None):
        self._permissions = {}
        if permissions:
            for group, allowed in permissions.items():
                self._permissions[f'{group}'] = bool(allowed)

    def is_permitted(self, required_permissions):
        """Return ``True`` when every required group is currently granted.

        ``required_permissions`` is an iterable of permission-group names (a
        cmdlet's declared ``permissions`` list). An empty/``None`` requirement
        always passes.
        """
        for group in _as_set(required_permissions):
            if not self._permissions.get(group, True):
                return False
        return True

    def allow(self, group):
        """Grant one permission group (the default state)."""
        self._permissions[f'{group}'] = True

    def deny(self, group):
        """Forbid one permission group."""
        self._permissions[f'{group}'] = False

    def reset(self):
        """Forget all overrides — grant every group again."""
        self._permissions.clear()

    def snapshot(self):
        """Return a plain dict copy of the current permission overrides."""
        return dict(self._permissions)


def _as_set(names):
    if names is None:
        return set()
    if isinstance(names, str):
        return {names}
    return set(names)


_SETTINGS = ContextVar('apqa_user_settings', default=None)


@contextmanager
def user_settings_scope(settings):
    """Make ``settings`` the active settings for one chain run.

    This uses a ``ContextVar`` so nested chain runs (``map``'s transform,
    ``where``'s predicate, operand chains) inherit the same settings without an
    extra parameter threaded through every cmdlet signature, and concurrent rule
    runs never mix their settings.
    """
    token = _SETTINGS.set(settings)
    try:
        yield settings
    finally:
        _SETTINGS.reset(token)


def current_user_settings():
    """The active settings for the current chain run, or ``None`` outside one."""
    return _SETTINGS.get()

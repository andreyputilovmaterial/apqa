"""Resolve folder (group) aliases for QC rules.

An alias binds a short ``name`` to the value produced by running its ``chain``
of cmdlets. Aliases live on a group (folder) and are inherited by descendant
groups, like a ``with`` statement: a folder's aliases are resolved once and then
shared by every rule inside that folder and its sub-folders.
"""

from .cmdlets.chain_runner import run_chain


def substitute(value, scope):
    """Replace alias-name strings in ``value`` with their resolved values.

    Recurses through mappings and lists (cmdlet chains and arbitrary ``args``
    values), so an alias can be referenced anywhere an argument value is allowed.
    The ``cmdlet`` key of a cmdlet step is left alone — a cmdlet name is not an
    alias reference — while its ``args`` are substituted normally.
    """
    if not scope:
        return value
    if isinstance(value, str):
        return scope.get(value, value)
    if isinstance(value, list):
        return [substitute(item, scope) for item in value]
    if isinstance(value, dict):
        return {
            key: (val if key == 'cmdlet' else substitute(val, scope))
            for key, val in value.items()
        }
    return value


class AliasScopeResolver:
    """Resolve each group's aliases once and cache the resulting scope."""

    def __init__(self, groups):
        self._groups = {group.id: group for group in groups}
        self._cache = {}
        self._resolving = set()

    def scope_for(self, group_id):
        """Return the effective alias scope for ``group_id`` (parent-scoped)."""
        if group_id not in self._groups:
            return {}
        if group_id in self._cache:
            return self._cache[group_id]
        if group_id in self._resolving:
            raise ValueError(
                f'group parent chain contains a cycle at {group_id!r}'
            )

        self._resolving.add(group_id)
        try:
            group = self._groups[group_id]
            parent_scope = (
                self.scope_for(group.parent)
                if group.parent in self._groups
                else {}
            )
            own = {}
            for alias in group.aliases:
                chain = substitute(alias['chain'], parent_scope)
                own[alias['name']] = run_chain(chain)
            scope = {**parent_scope, **own}
        finally:
            self._resolving.discard(group_id)

        self._cache[group_id] = scope
        return scope

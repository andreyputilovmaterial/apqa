"""Upgrade cmdlet/op names stored in older database files.

The logical/bitwise cmdlets and the comparison ops were renamed (``and`` →
``logical-and``, ``bit-and`` → ``bitwise-and``, ``eq`` → ``cmp-eq``, …). A
database file written before that rename still carries the old names, so the
DB processors rewrite them in memory when they *read* a rule/group. The file on
disk is left untouched — the upgraded names are persisted the next time the
rule/group is saved.

This is deliberately a read-time transform, not part of
:meth:`~.rule_base.Rule.from_dict` / :meth:`~.group_base.Group.from_dict`: the
constructors stay pure (they round-trip whatever they are given), while the
storage layer knows it is reading previously-saved data.
"""

# Comparison-op renames: old name -> current name.
OP_RENAMES = {
    'eq': 'cmp-eq',
    'ne': 'cmp-ne',
    'eq-unordered': 'cmp-eq-unordered',
    'lt': 'cmp-lt',
    'le': 'cmp-le',
    'gt': 'cmp-gt',
    'ge': 'cmp-ge',
    'contains': 'cmp-contains',
}

# Cmdlet renames: old name -> current name.
CMDLET_RENAMES = {
    'and': 'logical-and',
    'or': 'logical-or',
    'all': 'logical-all',
    'any': 'logical-any',
    'not': 'logical-not',
    'bit-and': 'bitwise-and',
    'bit-or': 'bitwise-or',
    'bit-xor': 'bitwise-xor',
    'bit-not': 'bitwise-not',
    'bit-lshift': 'bitwise-lshift',
    'bit-rshift': 'bitwise-rshift',
    'filter': 'exclude-deep-node',
    'matches': 'validate-text-matches',
}


def migrate_op_name(op):
    """Return the current name for ``op`` (the old name itself if unchanged)."""
    if op is None or op == '':
        return op
    return OP_RENAMES.get(f'{op}', f'{op}')


def _migrate_filter_args(migrated):
    """Convert a legacy ``filter`` step's ``ignorelist`` into ``rules``.

    ``filter`` was renamed to ``exclude-deep-node``, and its ``ignorelist`` (a
    flat list of exact full-path strings) became ``rules`` (a list of
    ``{name, type, pattern}`` mappings). The old exact-match behaviour maps to
    ``type: 'eq'``; each old path becomes both the display ``name`` and the
    ``pattern``.
    """
    args = migrated.get('args')
    if not isinstance(args, dict) or 'ignorelist' not in args:
        return
    ignorelist = args['ignorelist']
    if not isinstance(ignorelist, list):
        return
    rules = [
        {'name': path, 'type': 'eq', 'pattern': path}
        for path in ignorelist
        if isinstance(path, str)
    ]
    migrated_args = {
        key: item for key, item in args.items() if key != 'ignorelist'
    }
    migrated_args['rules'] = rules
    migrated['args'] = migrated_args


def _migrate_value(value):
    """Recursively rewrite any ``{'cmdlet': <name>, 'args': ...}`` step.

    A cmdlet chain (and its nested ``cmdlet-chain`` / ``cmdlet-chains`` args,
    e.g. ``and``/``or``/``bit-*`` ``operands`` or ``map``'s ``transform``) is a
    tree of mappings/lists; any mapping with a ``cmdlet`` key is a step and has
    its name upgraded. Everything else is passed through unchanged.
    """
    if isinstance(value, dict):
        if 'cmdlet' in value:
            migrated = dict(value)
            migrated['cmdlet'] = CMDLET_RENAMES.get(value.get('cmdlet'), value.get('cmdlet'))
            if isinstance(value.get('args'), dict):
                migrated['args'] = {
                    key: _migrate_value(arg_value)
                    for key, arg_value in value['args'].items()
                }
            if migrated['cmdlet'] == 'exclude-deep-node':
                _migrate_filter_args(migrated)
            return migrated
        return {key: _migrate_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_migrate_value(item) for item in value]
    return value


def migrate_chain(chain):
    """Return ``chain`` with every cmdlet name upgraded (non-list → unchanged)."""
    if not isinstance(chain, list):
        return chain
    return [_migrate_value(step) for step in chain]


def migrate_rule_dict(data):
    """Return a rule mapping with its ``op`` and ``left``/``right`` names upgraded."""
    if not isinstance(data, dict):
        return data
    migrated = dict(data)
    if data.get('op') is not None and f"{data['op']}" != '':
        migrated['op'] = migrate_op_name(data['op'])
    migrated['left'] = migrate_chain(data.get('left') or [])
    migrated['right'] = migrate_chain(data.get('right') or [])
    return migrated


def migrate_group_dict(data):
    """Return a group mapping with its alias chains upgraded."""
    if not isinstance(data, dict):
        return data
    migrated = dict(data)
    aliases = data.get('aliases') or []
    if isinstance(aliases, list):
        migrated['aliases'] = [_migrate_alias(alias) for alias in aliases]
    return migrated


def _migrate_alias(alias):
    if not isinstance(alias, dict):
        return alias
    migrated = dict(alias)
    migrated['chain'] = migrate_chain(alias.get('chain') or [])
    return migrated

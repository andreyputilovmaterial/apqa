"""Shared path-rule matching for the `exclude-*` cmdlets.

An **exclude rule** names nodes to remove from a block/collection tree by matching
their **data path** (the ``format_path`` notation from the value taxonomy). Both
`exclude-child` (direct children only) and `exclude-deep-node` (recursive) build
on the same rule shape and matcher, so the two cmdlets stay interchangeable.

A rule is a mapping::

    {'name': 'Skip Select labels', 'type': 'eq',
     'pattern': 'Fields.SnifferData.Fields.Cluster.Elements.Select',
     'case_insensitive': False}

- ``pattern`` (required) is the text matched against the rendered path;
- ``type`` (default ``eq``) is one of ``RULE_TYPES``;
- ``case_insensitive`` (default ``False``) folds case for the literal modes and
  adds ``re.IGNORECASE`` for ``regex``;
- ``name`` (optional) is a free-form display label.
"""

import re

from .value_types import format_path  # noqa: F401 - re-exported for compatibility

RULE_TYPES = ('eq', 'startswith', 'endswith', 'contains', 'regex')


def normalize_rules(rules):
    """Validate and normalize the ``rules`` arg into a list of rule mappings.

    ``None`` and an empty list both mean "remove nothing" and become ``[]``.
    Each rule must be a mapping with a non-empty string ``pattern``; ``type``
    must be one of ``RULE_TYPES``. Fails early with a readable error on a
    malformed rule.
    """
    if rules is None:
        return []
    if not isinstance(rules, list):
        raise TypeError('exclude rules must be a list of rule mappings')

    normalized = []
    for rule in rules:
        if not isinstance(rule, dict):
            raise TypeError('each exclude rule must be a mapping')
        pattern = rule.get('pattern')
        if pattern is None or f'{pattern}' == '':
            raise ValueError('each exclude rule needs a non-empty "pattern"')
        rule_type = rule.get('type', 'eq')
        if rule_type not in RULE_TYPES:
            raise ValueError(
                f'exclude rule type {rule_type!r} must be one of '
                f'{", ".join(RULE_TYPES)}'
            )
        normalized.append({
            'pattern': f'{pattern}',
            'type': rule_type,
            'case_insensitive': bool(rule.get('case_insensitive', False)),
            'name': rule.get('name'),
        })
    return normalized


def match_text(pattern, rule_type, case_insensitive, text):
    """Return ``True`` when ``text`` matches one rule.

    ``text`` is a rendered data path (``format_path`` notation). ``eq`` is a
    full exact match; ``startswith``/``endswith``/``contains`` are literal
    string predicates; ``regex`` is ``re.search``. ``case_insensitive`` folds
    case for the literal modes and adds ``re.IGNORECASE`` for regex.
    """
    if rule_type == 'regex':
        flags = re.IGNORECASE if case_insensitive else 0
        return re.search(pattern, text, flags) is not None

    haystack = text.lower() if case_insensitive else text
    needle = pattern.lower() if case_insensitive else pattern
    if rule_type == 'eq':
        return haystack == needle
    if rule_type == 'startswith':
        return haystack.startswith(needle)
    if rule_type == 'endswith':
        return haystack.endswith(needle)
    if rule_type == 'contains':
        return needle in haystack
    return False  # unreachable after normalize_rules


def matches_any_rule(path_text, rules):
    """Return ``True`` when ``path_text`` matches any normalized rule."""
    for rule in rules:
        if match_text(
            rule['pattern'], rule['type'], rule['case_insensitive'], path_text
        ):
            return True
    return False


def path_matches(index_path, name_path, rules):
    """Return ``True`` when either spelling of a node's data path matches a rule."""
    if matches_any_rule(format_path(index_path), rules):
        return True
    if name_path != index_path:
        return matches_any_rule(format_path(name_path), rules)
    return False

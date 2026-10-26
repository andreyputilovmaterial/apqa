"""Tests for folder (group) alias substitution and resolution (load_cases)."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.group_aliases import AliasScopeResolver, substitute
from src.tstsuite import load_cases


def test_substitute_replaces_alias_strings():
    scope = {'survey_mdd': {'fields': {}}, 'processed_data': [1, 2]}
    chain = [
        {'cmdlet': 'select-property', 'args': {'source': 'survey_mdd', 'name': 'x'}},
        {'cmdlet': 'literal', 'args': {'value': 'processed_data'}},
    ]
    out = substitute(chain, scope)
    assert out[0]['args']['source'] == {'fields': {}}
    assert out[0]['args']['name'] == 'x'
    assert out[1]['args']['value'] == [1, 2]


def test_substitute_skips_cmdlet_names():
    scope = {'count': 'SHOULD_NOT_APPLY'}
    out = substitute([{'cmdlet': 'count', 'args': {}}], scope)
    assert out[0]['cmdlet'] == 'count'


def test_substitute_leaves_unknown_strings():
    assert substitute(['plain'], {}) == ['plain']


def test_substitute_recurses_into_nested_structures():
    scope = {'A': 1}
    value = {
        'block': {'field': 'A'},
        'list': ['A', {'cmdlet': 'A', 'args': {'x': 'A'}}],
    }
    out = substitute(value, scope)
    assert out['block']['field'] == 1
    assert out['list'][0] == 1
    assert out['list'][1]['cmdlet'] == 'A'
    assert out['list'][1]['args']['x'] == 1


# ---- AliasScopeResolver ------------------------------------------------------

class _Group:
    def __init__(self, name, parent='', aliases=None):
        self.name = name
        self.parent = parent
        self.aliases = aliases or []


def _literal_alias(name, value):
    return {'name': name, 'chain': [{'cmdlet': 'literal', 'args': {'value': value}}]}


def test_resolver_resolves_once_and_inherits_from_parent():
    groups = [
        _Group('Root', '', [_literal_alias('a', 1)]),
        _Group('Child', 'Root', [_literal_alias('b', 2)]),
    ]
    resolver = AliasScopeResolver(groups)

    scope = resolver.scope_for('Child')
    assert scope == {'a': 1, 'b': 2}
    # Resolved once per group (the cache returns the same scope object).
    assert resolver.scope_for('Child') is scope


def test_resolver_child_shadows_parent_alias():
    groups = [
        _Group('Root', '', [_literal_alias('x', 1)]),
        _Group('Child', 'Root', [_literal_alias('x', 2)]),
    ]
    resolver = AliasScopeResolver(groups)
    assert resolver.scope_for('Child') == {'x': 2}


def test_resolver_unknown_group_returns_empty_scope():
    resolver = AliasScopeResolver([_Group('Root')])
    assert resolver.scope_for('Ghost') == {}


# ---- load_cases end-to-end ---------------------------------------------------

YAML = """\
groups:
  - name: Data
    aliases:
      - name: expected
        chain:
          - cmdlet: literal
            args:
              value: 42
rules:
  - name: ungrouped
    op: eq
    left:
      - cmdlet: literal
        args:
          value: expected
    right:
      - cmdlet: literal
        args:
          value: expected
  - name: grouped
    group: Data
    op: eq
    left:
      - cmdlet: literal
        args:
          value: expected
    right:
      - cmdlet: literal
        args:
          value: 42
"""


def test_load_cases_resolves_aliases_for_grouped_rules(tmp_path):
    db_file = tmp_path / 'project.yaml'
    db_file.write_text(YAML, encoding='utf-8')

    cases = list(load_cases(str(db_file)))
    by_name = {case.name: case for case in cases}

    # Ungrouped rules are untouched: `expected` stays a literal string.
    assert by_name['ungrouped'].left[0]['args']['value'] == 'expected'

    # Grouped rules have `expected` resolved to the alias value.
    assert by_name['grouped'].left[0]['args']['value'] == 42
    assert by_name['grouped'].right[0]['args']['value'] == 42


def test_load_cases_runs_grouped_rule_with_alias(tmp_path):
    db_file = tmp_path / 'project.yaml'
    db_file.write_text(YAML, encoding='utf-8')

    grouped = next(c for c in load_cases(str(db_file)) if c.name == 'grouped')
    assert grouped.run() is True

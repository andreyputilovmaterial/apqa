"""Tests for the in-memory user settings and cmdlet permission enforcement."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from src.user_settings import UserSettings
from src.rule_runner import run_rule, run_rule_with_report
from src.cmdlets.chain_runner import (
    ChainError,
    PermissionDeniedError,
    run_chain,
)


def _literal(value):
    return {'cmdlet': 'literal', 'args': {'value': value}}


def test_default_grants_every_group():
    settings = UserSettings()
    assert settings.is_permitted([]) is True
    assert settings.is_permitted(None) is True
    assert settings.is_permitted(['filesystem']) is True
    assert settings.is_permitted(['network']) is True
    assert settings.is_permitted(['filesystem', 'network']) is True


def test_deny_group_is_not_permitted():
    settings = UserSettings()
    settings.deny('filesystem')
    assert settings.is_permitted(['filesystem']) is False
    assert settings.is_permitted(['filesystem', 'network']) is False
    assert settings.is_permitted(['network']) is True


def test_init_with_permission_mapping():
    settings = UserSettings(permissions={'filesystem': False})
    assert settings.is_permitted(['filesystem']) is False
    assert settings.is_permitted(['network']) is True


def test_allow_and_reset():
    settings = UserSettings()
    settings.deny('filesystem')
    settings.allow('filesystem')
    assert settings.is_permitted(['filesystem']) is True
    settings.reset()
    assert settings.is_permitted(['filesystem']) is True


def test_snapshot():
    settings = UserSettings(permissions={'filesystem': False})
    assert settings.snapshot() == {'filesystem': False}


def test_cmdlet_runs_by_default(tmp_path):
    path = tmp_path / 'data.txt'
    path.write_text('hello', encoding='utf-8')
    rule = {
        'left': [{'cmdlet': 'get-content-text', 'args': {'path': str(path)}}],
        'op': 'cmp-eq',
        'right': [_literal('hello')],
    }
    assert run_rule(rule) is True


def test_denied_cmdlet_does_not_run():
    settings = UserSettings()
    settings.deny('filesystem')
    rule = {
        'left': [{'cmdlet': 'get-content-text', 'args': {'path': '/does/not/exist'}}],
        'op': 'cmp-eq',
        'right': [_literal('x')],
    }
    with pytest.raises(ChainError) as excinfo:
        run_rule(rule, settings=settings)
    assert 'requires permission group' in str(excinfo.value)
    assert isinstance(excinfo.value.__cause__, PermissionDeniedError)


def test_denied_cmdlet_does_not_run_with_report():
    settings = UserSettings()
    settings.deny('filesystem')
    rule = {
        'left': [{'cmdlet': 'get-content-text', 'args': {'path': '/does/not/exist'}}],
        'op': 'cmp-eq',
        'right': [_literal('x')],
    }
    with pytest.raises(ChainError):
        run_rule_with_report(rule, settings=settings)


def test_denied_extended_dependency_group_blocks_cmdlet():
    # Denying the `deps-extended` umbrella forbids a cmdlet that loads a
    # non-stdlib library, before its body (and the lazy import) ever runs.
    settings = UserSettings()
    settings.deny('deps-extended')
    rule = {
        'left': [
            {'cmdlet': 'get-content-excel', 'args': {'path': '/does/not/exist.xlsx'}},
        ],
        'op': 'cmp-eq',
        'right': [_literal(1)],
    }
    with pytest.raises(ChainError) as excinfo:
        run_rule(rule, settings=settings)
    assert 'requires permission group' in str(excinfo.value)
    assert 'deps-extended' in str(excinfo.value)
    assert isinstance(excinfo.value.__cause__, PermissionDeniedError)


def test_nested_chain_cmdlet_is_gated():
    settings = UserSettings()
    settings.deny('filesystem')
    rule = {
        'left': [
            _literal([1]),
            {
                'cmdlet': 'foreach-item',
                'args': {
                    'transform': [
                        {'cmdlet': 'get-content-text', 'args': {'path': '/does/not/exist'}},
                    ],
                },
            },
        ],
        'op': 'cmp-eq',
        'right': [_literal([None])],
    }
    with pytest.raises(ChainError) as excinfo:
        run_rule(rule, settings=settings)
    assert 'requires permission group' in str(excinfo.value)


def test_run_chain_explicit_settings():
    settings = UserSettings()
    settings.deny('network')
    with pytest.raises(ChainError) as excinfo:
        run_chain(
            [{'cmdlet': 'get-content-network-fetch'}],
            initial='https://example.com',
            settings=settings,
        )
    assert 'requires permission group' in str(excinfo.value)

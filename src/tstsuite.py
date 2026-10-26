
import os

from collections.abc import Iterable

from .db_processors import DBFile
from .db_processors.rule_base import Rule
from .group_aliases import AliasScopeResolver, substitute


DB_FILE_ENV_VAR_NAME = "APQA_DB_FILE"



def read_resource_path_from_env():
    db_file = os.environ.get(DB_FILE_ENV_VAR_NAME)
    if not db_file:
        # raise RuntimeError("APQA_DB_FILE environment variable is not set")
        return None
    return db_file


def load_cases(resource_path=None) -> Iterable:
    if resource_path is None:
        resource_path = read_resource_path_from_env()
    if not resource_path:
        raise RuntimeError('db_file resource_path is not provided')
    try:
        dbfile = DBFile(resource_path)
    except Exception as e:
        raise RuntimeError(f'db_file: can\'t load file: {resource_path}: {e}') from e

    groups = dbfile.list_groups()
    resolver = AliasScopeResolver(groups)
    group_ids = {group.id for group in groups}

    for rule in dbfile.list_rules():
        if rule.group in group_ids:
            yield _rule_with_scope(rule, resolver.scope_for(rule.group))
        else:
            yield rule


def _rule_with_scope(rule, scope):
    """Return a copy of ``rule`` with folder aliases resolved into its chains."""
    if not scope:
        return rule
    substituted = Rule.from_dict(rule.to_dict())
    substituted.left = substitute(rule.left, scope)
    substituted.right = substitute(rule.right, scope)
    return substituted


def run_tst_case(rule):
    result = rule.run()
    if result is not True:
        raise AssertionError(f'QC rule failed: {rule.name} (result: {result})')
    return None


def markers_for(rule):
    meta = getattr(rule, 'meta', None) or {}
    markers = meta.get('markers') or []
    if isinstance(markers, str):
        markers = [markers]
    return [f'{marker}' for marker in markers]


def pytest_param_for(rule):
    import pytest
    markers = markers_for(rule)
    marks = []
    if 'skip' in markers:
        marks.append(pytest.mark.skip(reason="rule marked 'skip'"))
    if 'xfail' in markers:
        marks.append(pytest.mark.xfail(reason="rule marked 'xfail'", strict=False))
    return pytest.param(rule, id=rule.id, marks=marks)


def load_case_params(resource_path=None) -> Iterable:
    for rule in load_cases(resource_path):
        yield pytest_param_for(rule)




import os

from collections.abc import Iterable

from .db_processors import DBFile


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
    yield from dbfile.rules


def run_tst_case(rule):
    rule.run()
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
    return pytest.param(rule, id=rule.name, marks=marks)


def load_case_params(resource_path=None) -> Iterable:
    for rule in load_cases(resource_path):
        yield pytest_param_for(rule)



"""Tests for the rule CRUD HTTP endpoint (/qc/rules...)."""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from src.db_processors import DBFile
from src.frontend.endpoints_rule_crud import handle_rule_crud
from src.webserver_engine.webserve.src.common_defs import WebResponse


class FakeRequest:
    """Minimal stand-in for BaseHTTPRequestHandler."""

    def __init__(self, method, path, body=b''):
        self.command = method
        self.path = path
        self.headers = {}
        self._body = body
        self.request_body = self

    def read(self):
        return self._body


@pytest.fixture
def config(tmp_path):
    db_file = tmp_path / 'projects.yaml'
    db_file.write_text('[]', encoding='utf-8')
    return {'iface': {'WebResponse': WebResponse, 'db_file': DBFile(str(db_file))}}


def call(config, method, path, body=None):
    if body is None:
        raw = b''
    elif isinstance(body, dict):
        raw = json.dumps(body).encode('utf-8')
    else:
        raw = body
    resp = handle_rule_crud(FakeRequest(method, path, raw), config)
    data = json.loads(resp.body) if resp.body else None
    return resp.status_code, data


def test_list_empty(config):
    status, data = call(config, 'GET', '/qc/rules')
    assert status == 200
    assert data == {'rules': []}


def test_create_and_list(config):
    status, data = call(config, 'POST', '/qc/rules', {'name': 'r1', 'op': 'eq'})
    assert status == 201
    assert data['rule']['name'] == 'r1'

    status, data = call(config, 'GET', '/qc/rules')
    assert status == 200
    assert [r['name'] for r in data['rules']] == ['r1']


def test_create_duplicate(config):
    call(config, 'POST', '/qc/rules', {'name': 'r1'})
    status, data = call(config, 'POST', '/qc/rules', {'name': 'r1'})
    assert status == 409


def test_create_missing_name(config):
    status, data = call(config, 'POST', '/qc/rules', {'op': 'eq'})
    assert status == 400


def test_create_invalid_json(config):
    status, data = call(config, 'POST', '/qc/rules', b'{not json')
    assert status == 400


def test_get_rule(config):
    call(config, 'POST', '/qc/rules', {'name': 'r1', 'op': 'eq'})
    status, data = call(config, 'GET', '/qc/rules/r1')
    assert status == 200
    assert data['rule']['op'] == 'eq'


def test_get_rule_missing(config):
    status, data = call(config, 'GET', '/qc/rules/nope')
    assert status == 404


def test_update_rule(config):
    call(config, 'POST', '/qc/rules', {'name': 'r1', 'op': 'eq'})
    status, data = call(config, 'PUT', '/qc/rules/r1', {'op': 'lt'})
    assert status == 200
    assert data['rule']['op'] == 'lt'


def test_update_rule_rejects_name_change(config):
    call(config, 'POST', '/qc/rules', {'name': 'r1'})
    status, data = call(config, 'PUT', '/qc/rules/r1', {'name': 'r2'})
    assert status == 400


def test_delete_rule(config):
    call(config, 'POST', '/qc/rules', {'name': 'r1'})
    status, data = call(config, 'DELETE', '/qc/rules/r1')
    assert status == 200
    assert data['rule']['name'] == 'r1'

    status, data = call(config, 'GET', '/qc/rules/r1')
    assert status == 404


def test_delete_rule_missing(config):
    status, data = call(config, 'DELETE', '/qc/rules/nope')
    assert status == 404


def test_rename_rule(config):
    call(config, 'POST', '/qc/rules', {'name': 'r1'})
    status, data = call(config, 'POST', '/qc/rules/r1/rename', {'new_name': 'r2'})
    assert status == 200
    assert data['rule']['name'] == 'r2'


def test_rename_rule_duplicate(config):
    call(config, 'POST', '/qc/rules', {'name': 'r1'})
    call(config, 'POST', '/qc/rules', {'name': 'r2'})
    status, data = call(config, 'POST', '/qc/rules/r1/rename', {'new_name': 'r2'})
    assert status == 409


def test_rename_rule_missing_new_name(config):
    call(config, 'POST', '/qc/rules', {'name': 'r1'})
    status, data = call(config, 'POST', '/qc/rules/r1/rename', {})
    assert status == 400


def test_unknown_method(config):
    status, data = call(config, 'PATCH', '/qc/rules')
    assert status == 405


def test_unknown_path(config):
    status, data = call(config, 'GET', '/qc/rules/r1/extra')
    assert status == 405


def test_create_rule_with_group(config):
    config['iface']['db_file'].add_group({'name': 'Data'})
    status, data = call(config, 'POST', '/qc/rules', {'name': 'r1', 'group': 'Data'})
    assert status == 201
    assert data['rule']['group'] == 'Data'


def test_create_rule_with_missing_group(config):
    status, data = call(config, 'POST', '/qc/rules', {'name': 'r1', 'group': 'Nope'})
    assert status == 400


def test_update_rule_with_missing_group(config):
    call(config, 'POST', '/qc/rules', {'name': 'r1'})
    status, data = call(config, 'PUT', '/qc/rules/r1', {'group': 'Nope'})
    assert status == 400


def test_update_rule_with_group(config):
    call(config, 'POST', '/qc/rules', {'name': 'r1'})
    config['iface']['db_file'].add_group({'name': 'Data'})
    status, data = call(config, 'PUT', '/qc/rules/r1', {'group': 'Data'})
    assert status == 200
    assert data['rule']['group'] == 'Data'

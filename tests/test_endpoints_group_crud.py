"""Tests for the group (folder) CRUD HTTP endpoint (/qc/groups...)."""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from src.db_processors import DBFile
from src.frontend.endpoints_group_crud import handle_group_crud
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
    db_file.write_text('{}', encoding='utf-8')
    return {'iface': {'WebResponse': WebResponse, 'db_file': DBFile(str(db_file))}}


def call(config, method, path, body=None):
    if body is None:
        raw = b''
    elif isinstance(body, dict):
        raw = json.dumps(body).encode('utf-8')
    else:
        raw = body
    resp = handle_group_crud(FakeRequest(method, path, raw), config)
    data = json.loads(resp.body) if resp.body else None
    return resp.status_code, data


def test_list_empty(config):
    status, data = call(config, 'GET', '/qc/groups')
    assert status == 200
    assert data == {'groups': []}


def test_create_and_list(config):
    status, data = call(config, 'POST', '/qc/groups', {'name': 'Data'})
    assert status == 201
    assert data['group']['name'] == 'Data'

    status, data = call(config, 'GET', '/qc/groups')
    assert status == 200
    assert [g['name'] for g in data['groups']] == ['Data']


def test_create_duplicate(config):
    call(config, 'POST', '/qc/groups', {'name': 'Data'})
    status, data = call(config, 'POST', '/qc/groups', {'name': 'Data'})
    assert status == 409


def test_create_missing_name(config):
    status, data = call(config, 'POST', '/qc/groups', {'parent': ''})
    assert status == 400


def test_create_invalid_parent(config):
    status, data = call(config, 'POST', '/qc/groups', {'name': 'Child', 'parent': 'Nope'})
    assert status == 400


def test_get_group(config):
    call(config, 'POST', '/qc/groups', {'name': 'Data'})
    status, data = call(config, 'GET', '/qc/groups/Data')
    assert status == 200
    assert data['group']['name'] == 'Data'


def test_get_group_missing(config):
    status, data = call(config, 'GET', '/qc/groups/nope')
    assert status == 404


def test_update_group(config):
    call(config, 'POST', '/qc/groups', {'name': 'Data'})
    call(config, 'POST', '/qc/groups', {'name': 'Metadata'})
    status, data = call(config, 'PUT', '/qc/groups/Metadata', {'parent': 'Data'})
    assert status == 200
    assert data['group']['parent'] == 'Data'


def test_create_group_with_aliases(config):
    status, data = call(config, 'POST', '/qc/groups', {
        'name': 'Data',
        'aliases': [{'name': 'x', 'chain': []}],
    })
    assert status == 201
    assert data['group']['aliases'][0]['name'] == 'x'


def test_update_group_aliases(config):
    call(config, 'POST', '/qc/groups', {'name': 'Data'})
    status, data = call(config, 'PUT', '/qc/groups/Data', {
        'aliases': [{'name': 'x', 'chain': [{'cmdlet': 'literal', 'args': {'value': 1}}]}],
    })
    assert status == 200
    assert data['group']['aliases'][0]['name'] == 'x'


def test_update_group_rejects_name_change(config):
    call(config, 'POST', '/qc/groups', {'name': 'Data'})
    status, data = call(config, 'PUT', '/qc/groups/Data', {'name': 'Other'})
    assert status == 400


def test_delete_group(config):
    call(config, 'POST', '/qc/groups', {'name': 'Data'})
    status, data = call(config, 'DELETE', '/qc/groups/Data')
    assert status == 200
    assert data['group']['name'] == 'Data'

    status, data = call(config, 'GET', '/qc/groups/Data')
    assert status == 404


def test_delete_non_empty_group(config):
    call(config, 'POST', '/qc/groups', {'name': 'Data'})
    config['iface']['db_file'].add_rule({'name': 'r1', 'group': 'Data'})
    status, data = call(config, 'DELETE', '/qc/groups/Data')
    assert status == 409


def test_delete_group_missing(config):
    status, data = call(config, 'DELETE', '/qc/groups/nope')
    assert status == 404


def test_rename_group(config):
    call(config, 'POST', '/qc/groups', {'name': 'Data'})
    status, data = call(config, 'POST', '/qc/groups/Data/rename', {'new_name': 'Core'})
    assert status == 200
    assert data['group']['name'] == 'Core'


def test_rename_group_duplicate(config):
    call(config, 'POST', '/qc/groups', {'name': 'Data'})
    call(config, 'POST', '/qc/groups', {'name': 'Core'})
    status, data = call(config, 'POST', '/qc/groups/Data/rename', {'new_name': 'Core'})
    assert status == 409


def test_rename_group_missing_new_name(config):
    call(config, 'POST', '/qc/groups', {'name': 'Data'})
    status, data = call(config, 'POST', '/qc/groups/Data/rename', {})
    assert status == 400


def test_unknown_method(config):
    status, data = call(config, 'PATCH', '/qc/groups')
    assert status == 405


def test_unknown_path(config):
    status, data = call(config, 'GET', '/qc/groups/Data/extra')
    assert status == 405

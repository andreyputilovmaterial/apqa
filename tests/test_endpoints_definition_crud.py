"""Tests for the definition (alias) CRUD HTTP endpoint (/qc/definitions...)."""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from src.db_processors import DBFile
from src.frontend.endpoints_definition_crud import handle_definition_crud
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
    resp = handle_definition_crud(FakeRequest(method, path, raw), config)
    data = json.loads(resp.body) if resp.body else None
    return resp.status_code, data


def test_list_empty(config):
    status, data = call(config, 'GET', '/qc/definitions')
    assert status == 200
    assert data == {'definitions': []}


def test_create_and_list(config):
    status, data = call(config, 'POST', '/qc/definitions', {'name': 'PROCESSED_DATA', 'value': '/data/a.db'})
    assert status == 201
    assert data['definition']['name'] == 'PROCESSED_DATA'

    status, data = call(config, 'GET', '/qc/definitions')
    assert status == 200
    assert [d['name'] for d in data['definitions']] == ['PROCESSED_DATA']


def test_create_duplicate(config):
    call(config, 'POST', '/qc/definitions', {'name': 'PROCESSED_DATA'})
    status, data = call(config, 'POST', '/qc/definitions', {'name': 'PROCESSED_DATA'})
    assert status == 409


def test_create_missing_name(config):
    status, data = call(config, 'POST', '/qc/definitions', {'value': '/x'})
    assert status == 400


def test_create_invalid_json(config):
    status, data = call(config, 'POST', '/qc/definitions', b'{not json')
    assert status == 400


def test_get_definition(config):
    call(config, 'POST', '/qc/definitions', {'name': 'PROCESSED_DATA', 'value': '/data/a.db'})
    status, data = call(config, 'GET', '/qc/definitions/PROCESSED_DATA')
    assert status == 200
    assert data['definition']['value'] == '/data/a.db'


def test_get_definition_missing(config):
    status, data = call(config, 'GET', '/qc/definitions/nope')
    assert status == 404


def test_update_definition(config):
    call(config, 'POST', '/qc/definitions', {'name': 'PROCESSED_DATA', 'value': '/data/a.db'})
    status, data = call(config, 'PUT', '/qc/definitions/PROCESSED_DATA', {'value': '/data/b.db'})
    assert status == 200
    assert data['definition']['value'] == '/data/b.db'


def test_update_definition_rejects_name_change(config):
    call(config, 'POST', '/qc/definitions', {'name': 'PROCESSED_DATA'})
    status, data = call(config, 'PUT', '/qc/definitions/PROCESSED_DATA', {'name': 'OTHER'})
    assert status == 400


def test_delete_definition(config):
    call(config, 'POST', '/qc/definitions', {'name': 'PROCESSED_DATA'})
    status, data = call(config, 'DELETE', '/qc/definitions/PROCESSED_DATA')
    assert status == 200
    assert data['definition']['name'] == 'PROCESSED_DATA'

    status, data = call(config, 'GET', '/qc/definitions/PROCESSED_DATA')
    assert status == 404


def test_delete_definition_missing(config):
    status, data = call(config, 'DELETE', '/qc/definitions/nope')
    assert status == 404


def test_rename_definition(config):
    call(config, 'POST', '/qc/definitions', {'name': 'PROCESSED_DATA'})
    status, data = call(config, 'POST', '/qc/definitions/PROCESSED_DATA/rename', {'new_name': 'DATA'})
    assert status == 200
    assert data['definition']['name'] == 'DATA'


def test_rename_definition_duplicate(config):
    call(config, 'POST', '/qc/definitions', {'name': 'PROCESSED_DATA'})
    call(config, 'POST', '/qc/definitions', {'name': 'DATA'})
    status, data = call(config, 'POST', '/qc/definitions/PROCESSED_DATA/rename', {'new_name': 'DATA'})
    assert status == 409


def test_rename_definition_missing_new_name(config):
    call(config, 'POST', '/qc/definitions', {'name': 'PROCESSED_DATA'})
    status, data = call(config, 'POST', '/qc/definitions/PROCESSED_DATA/rename', {})
    assert status == 400


def test_unknown_method(config):
    status, data = call(config, 'PATCH', '/qc/definitions')
    assert status == 405


def test_unknown_path(config):
    status, data = call(config, 'GET', '/qc/definitions/PROCESSED_DATA/extra')
    assert status == 405

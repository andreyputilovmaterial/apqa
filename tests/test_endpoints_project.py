"""Tests for the project metadata HTTP endpoint (/qc/project)."""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from src.db_processors import DBFile
from src.frontend.endpoints_project import handle_project_crud
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
    resp = handle_project_crud(FakeRequest(method, path, raw), config)
    data = json.loads(resp.body) if resp.body else None
    return resp.status_code, data


def test_get_project_empty(config):
    status, data = call(config, 'GET', '/qc/project')
    assert status == 200
    assert data == {'project': {'name': '', 'comment': '', 'meta': {}}}


def test_update_and_get_project(config):
    status, data = call(config, 'PUT', '/qc/project', {
        'name': 'Disney Brand Health Study',
        'comment': 'a note',
        'meta': {'created_by': 'apqa'},
    })
    assert status == 200
    assert data['project']['name'] == 'Disney Brand Health Study'
    assert data['project']['comment'] == 'a note'
    assert data['project']['meta'] == {'created_by': 'apqa'}

    status, data = call(config, 'GET', '/qc/project')
    assert status == 200
    assert data['project']['name'] == 'Disney Brand Health Study'


def test_update_project_is_persisted(config):
    call(config, 'PUT', '/qc/project', {'name': 'Saved', 'comment': 'kept'})

    reloaded = DBFile(str(config['iface']['db_file'].resource_path))
    assert reloaded.get_project().name == 'Saved'
    assert reloaded.get_project().comment == 'kept'


def test_update_project_invalid_json(config):
    status, data = call(config, 'PUT', '/qc/project', b'{not json')
    assert status == 400


def test_update_project_unknown_field(config):
    status, data = call(config, 'PUT', '/qc/project', {'bogus': 1})
    assert status == 400
    assert 'unknown project field' in data['error']


def test_unknown_method(config):
    status, data = call(config, 'POST', '/qc/project')
    assert status == 405


def test_unknown_path(config):
    status, data = call(config, 'GET', '/qc/project/extra')
    assert status == 405

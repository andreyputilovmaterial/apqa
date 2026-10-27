"""Tests for the cmdlet/op editor-metadata endpoint."""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from src.cmdlets.meta import get_cmdlet_metadata
from src.frontend.endpoints_functionality import handle_functionality
from src.webserver_engine.webserve.src.common_defs import WebResponse


class FakeRequest:
    def __init__(self, method, path, body=b''):
        self.command = method
        self.path = path
        self._body = body
        self.request_body = self

    def read(self):
        return self._body


@pytest.fixture
def config():
    return {
        'iface': {
            'WebResponse': WebResponse,
            'get_cmdlet_metadata': get_cmdlet_metadata,
        },
    }


def test_metadata_shape():
    metadata = get_cmdlet_metadata()
    assert set(metadata) == {'cmdlets', 'ops'}
    assert isinstance(metadata['cmdlets'], list)
    assert isinstance(metadata['ops'], list)


def test_every_cmdlet_has_editor_fields():
    for cmdlet in get_cmdlet_metadata()['cmdlets']:
        assert cmdlet['name']
        assert cmdlet['kind'] in ('source', 'processor', 'terminal')
        assert isinstance(cmdlet['args'], list)
        assert isinstance(cmdlet['help'], str)


def test_source_readers_are_marked_as_sources():
    kinds = {c['name']: c['kind'] for c in get_cmdlet_metadata()['cmdlets']}
    assert kinds['get-content-excel'] == 'source'
    assert kinds['get-content-mdd'] == 'source'
    assert kinds['literal'] == 'source'
    # Processors cannot be the first cmdlet in a chain.
    assert kinds['as-date'] == 'processor'
    assert kinds['count'] == 'processor'
    assert kinds['is-sysmissing'] == 'terminal'


def test_comparison_ops_and_op_args():
    ops = {o['name']: o for o in get_cmdlet_metadata()['ops']}
    for name in ('eq', 'ne', 'eq-unordered', 'lt', 'le', 'gt', 'ge', 'contains'):
        assert name in ops
    eq_args = {a['name']: a for a in ops['eq']['op_args']}
    assert eq_args['unordered_arrays']['type'] == 'boolean'


def test_endpoint_returns_metadata(config):
    resp = handle_functionality(FakeRequest('GET', '/functionality/cmdlet-metadata'), config)
    assert resp.status_code == 200
    data = json.loads(resp.body)
    assert set(data) == {'cmdlets', 'ops'}
    assert any(c['name'] == 'get-content-excel' for c in data['cmdlets'])


def test_endpoint_metadata_unavailable():
    config = {'iface': {'WebResponse': WebResponse}}
    resp = handle_functionality(FakeRequest('GET', '/functionality/cmdlet-metadata'), config)
    assert resp.status_code == 404

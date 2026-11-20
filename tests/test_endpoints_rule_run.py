"""Tests for the rule-run HTTP endpoint (POST /tests/run)."""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.frontend.endpoints_qctests_run import handle_qcrule_run
from src.webserver_engine.webserve.src.common_defs import WebResponse
from src.rule_runner import run_rule, run_rule_with_report


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


def make_config():
    return {'iface': {'WebResponse': WebResponse, 'run_rule': run_rule}}


def make_config_with_report():
    return {
        'iface': {
            'WebResponse': WebResponse,
            'run_rule': run_rule,
            'run_rule_with_report': run_rule_with_report,
        },
    }


def call(config, method, path, body=None):
    if body is None:
        raw = b''
    elif isinstance(body, dict):
        raw = json.dumps(body).encode('utf-8')
    else:
        raw = body
    resp = handle_qcrule_run(FakeRequest(method, path, raw), config, added_data='/tests/run')
    data = json.loads(resp.body) if resp.body else None
    return resp.status_code, data


def _literal(value):
    return {'cmdlet': 'literal', 'args': {'value': value}}


def test_run_true():
    rule = {'left': [_literal(1)], 'op': 'cmp-eq', 'right': [_literal(1)]}
    status, data = call(make_config(), 'POST', '/tests/run', rule)
    assert status == 200
    assert data == {'result': True}


def test_run_false():
    rule = {'left': [_literal(1)], 'op': 'cmp-eq', 'right': [_literal(2)]}
    status, data = call(make_config(), 'POST', '/tests/run', rule)
    assert status == 200
    assert data == {'result': False}


def test_run_true_with_report_has_no_notes_key():
    rule = {'left': [_literal(1)], 'op': 'cmp-eq', 'right': [_literal(1)]}
    status, data = call(
        make_config_with_report(), 'POST', '/tests/run', rule
    )
    assert status == 200
    assert data == {'result': True}


def test_run_false_with_report_includes_notes():
    block = {'Fields': {'A': {'Label': 'a & b'}}}
    rule = {
        'left': [
            {'cmdlet': 'literal', 'args': {'value': block}},
            {'cmdlet': 'validate-xml-compatible'},
        ],
        'op': 'cmp-eq',
        'right': [_literal(True)],
    }
    status, data = call(
        make_config_with_report(), 'POST', '/tests/run', rule
    )
    assert status == 200
    assert data['result'] is False
    assert data['notes'][0]['path'] == ['Fields', 'A', 'Label']


def test_invalid_json():
    status, data = call(make_config(), 'POST', '/tests/run', b'{not json')
    assert status == 400
    assert 'error' in data


def test_non_object_body():
    status, data = call(make_config(), 'POST', '/tests/run', b'[1,2,3]')
    assert status == 400
    assert 'error' in data


def test_runner_error_is_4xx_with_message():
    rule = {'left': [{'cmdlet': 'nope'}], 'op': 'cmp-eq', 'right': [_literal(1)]}
    status, data = call(make_config(), 'POST', '/tests/run', rule)
    assert 400 <= status < 500
    assert 'cmdlet not found' in data['error']
    assert 'traceback' in data
    assert 'cmdlet not found' in data['traceback']


def test_wrong_method():
    status, data = call(make_config(), 'GET', '/tests/run')
    assert status == 405


def test_runner_missing_in_config():
    config = make_config()
    config['iface'].pop('run_rule')
    status, data = call(config, 'POST', '/tests/run', {'left': [], 'op': 'cmp-eq', 'right': []})
    assert status == 404

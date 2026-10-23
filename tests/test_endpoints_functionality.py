"""Tests for the /functionality... endpoints."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.frontend.endpoints_functionality import handle_functionality
from src.webserver_engine.webserve.src.common_defs import WebResponse


class FakeRequest:
    """Minimal stand-in for BaseHTTPRequestHandler."""

    def __init__(self, method, path):
        self.command = method
        self.path = path
        self.headers = {}


def make_config():
    return {
        'time_start': datetime(2026, 10, 23, 7, 29, 0, tzinfo=timezone.utc),
        'script_name': 'apqa ui script',
        'credentials:year': '2026',
        'db_file': '/tmp/projects.sqlite3',
        'http_address': 'http://localhost:5180',
        'app_config': {'is_webserver_multithreaded': True},
        'iface': {
            'WebResponse': WebResponse,
            'get_help_pages': lambda: '# Help\n\nhello world',
        },
    }


def call(config, method, path):
    resp = handle_functionality(FakeRequest(method, path), config)
    data = json.loads(resp.body) if resp.body else None
    return resp, data


def test_config_returns_json_without_iface():
    resp, data = call(make_config(), 'GET', '/functionality/config')
    assert resp.status_code == 200
    assert resp.content_type == 'application/json'
    assert 'iface' not in data
    assert data['time_start'] == '2026-10-23T07:29:00+00:00'
    assert data['script_name'] == 'apqa ui script'
    assert data['db_file'] == '/tmp/projects.sqlite3'


def test_config_dates_are_iso_utc_strings():
    resp, data = call(make_config(), 'GET', '/functionality/config')
    assert isinstance(data['time_start'], str)
    assert data['time_start'].endswith('+00:00')


def test_help_pages_endpoint():
    resp, data = call(make_config(), 'GET', '/functionality/help-pages')
    assert resp.status_code == 200
    assert resp.content_type == 'application/json'
    assert data == {'help_pages': '# Help\n\nhello world'}


def test_help_pages_missing_callback():
    config = make_config()
    config['iface'].pop('get_help_pages')
    resp, data = call(config, 'GET', '/functionality/help-pages')
    assert resp.status_code == 404


def test_config_unknown_method():
    resp, data = call(make_config(), 'POST', '/functionality/config')
    assert resp.status_code == 405


def test_unknown_path():
    resp, data = call(make_config(), 'GET', '/functionality/nope')
    assert resp.status_code == 405

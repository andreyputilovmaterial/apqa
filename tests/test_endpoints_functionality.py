"""Tests for the /functionality grab-bag endpoint (always 404)."""

import json
import sys
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
    return {'iface': {'WebResponse': WebResponse}}


def call(config, method, path):
    resp = handle_functionality(FakeRequest(method, path), config, added_data='/functionality')
    data = json.loads(resp.body) if resp.body else None
    return resp, data


def test_functionality_root_is_404():
    resp, data = call(make_config(), 'GET', '/functionality')
    assert resp.status_code == 404
    assert 'grab-bag' in data['error']


def test_functionality_subpath_is_404():
    resp, data = call(make_config(), 'GET', '/functionality/nope')
    assert resp.status_code == 404


def test_functionality_any_method_is_404():
    resp, data = call(make_config(), 'POST', '/functionality/config')
    assert resp.status_code == 404


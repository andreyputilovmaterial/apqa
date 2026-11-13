"""Tests for the backend liveness endpoint (/health)."""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from src.frontend.endpoints_health import handle_health
from src.webserver_engine.webserve.src.common_defs import WebResponse


class FakeRequest:
    """Minimal stand-in for BaseHTTPRequestHandler."""

    def __init__(self, method, path):
        self.command = method
        self.path = path
        self.headers = {}
        self.request_body = self

    def read(self):
        return b''


@pytest.fixture
def config():
    return {'iface': {'WebResponse': WebResponse}}


def call(config, method, path):
    resp = handle_health(FakeRequest(method, path), config)
    data = json.loads(resp.body) if resp.body else None
    return resp.status_code, data


def test_health_get_returns_ok(config):
    status, data = call(config, 'GET', '/health')
    assert status == 200
    assert data == {'status': 'ok'}


def test_health_head_returns_ok(config):
    # The webserver engine strips the body for HEAD, but the renderer must still
    # report 200 so a HEAD probe reads as "alive".
    status, data = call(config, 'HEAD', '/health')
    assert status == 200


def test_health_unknown_method(config):
    status, data = call(config, 'POST', '/health')
    assert status == 405


def test_health_unknown_path(config):
    status, data = call(config, 'GET', '/health/extra')
    assert status == 405

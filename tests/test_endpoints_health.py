"""Tests for the backend liveness endpoint (/health)."""

import functools
import http.client
import json
import socket
import sys
import threading
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
    resp = handle_health(FakeRequest(method, path), config, added_data='/health')
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


def test_health_head_through_webserver_engine(config):
    # Regression: the renderer returns body=None for HEAD, and the webserver
    # engine must turn that into an empty binary body instead of trying to
    # .encode() it (which previously raised AttributeError on HEAD /health).
    from src.webserver_engine.webserve.src.webserver import Webserver

    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]

    server_config = {
        "http_host": "127.0.0.1",
        "http_port": port,
        "iface": {"WebResponse": WebResponse},
    }
    srv = Webserver(server_config, is_threading=True)
    srv.assign_handlers(
        {"/health": functools.partial(handle_health, added_data="/health")}
    )
    thread = threading.Thread(target=srv.run, daemon=True)
    thread.start()

    for _ in range(100):
        if srv.server is not None:
            break
        threading.Event().wait(0.05)
    else:
        raise RuntimeError("webserver did not start")

    server = srv.server
    try:
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        conn.request("HEAD", "/health")
        resp = conn.getresponse()
        assert resp.status == 200
        assert resp.read() == b""
        conn.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_health_unknown_method(config):
    status, data = call(config, 'POST', '/health')
    assert status == 405


def test_health_unknown_path(config):
    status, data = call(config, 'GET', '/health/extra')
    assert status == 405

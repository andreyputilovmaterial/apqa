"""Tests for --config-webserver-port (src/webserver_config.py)."""

import socket
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from src.webserver_config import (
    DEFAULT_PORT,
    parse_webserver_port,
    select_webserver_port,
)


def _occupied_port():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    sock.listen(1)
    return sock, sock.getsockname()[1]


def _unused_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_parse_none_is_default():
    assert parse_webserver_port(None) == (DEFAULT_PORT, True)


def test_parse_fixed_port():
    assert parse_webserver_port("6000") == (6000, False)
    assert parse_webserver_port(6000) == (6000, False)


def test_parse_auto_increment():
    assert parse_webserver_port("6000+") == (6000, True)


def test_parse_rejects_non_numeric():
    with pytest.raises(ValueError, match="port number"):
        parse_webserver_port("abc")


def test_parse_rejects_out_of_range():
    with pytest.raises(ValueError, match="out of range"):
        parse_webserver_port("0")
    with pytest.raises(ValueError, match="out of range"):
        parse_webserver_port("70000")


def test_select_fixed_port_returns_free_port():
    port = _unused_port()
    assert select_webserver_port("127.0.0.1", str(port)) == port


def test_select_fixed_port_fails_when_occupied():
    sock, port = _occupied_port()
    try:
        with pytest.raises(RuntimeError, match="already in use"):
            select_webserver_port("127.0.0.1", str(port))
    finally:
        sock.close()


def test_select_auto_increment_skips_occupied():
    sock, port = _occupied_port()
    try:
        result = select_webserver_port("127.0.0.1", f"{port}+")
        assert result >= port
        assert result != port
    finally:
        sock.close()

"""Tests for the network request cmdlets (fetch + validate)."""

import io
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from src.cmdlets import cmdlets


def _fetch(value, args=None):
    return cmdlets.get('get-content-network-fetch')(value, args or {})


def _validate(value):
    return cmdlets.get('validate-network-request-result')(value, {})


class FakeHeaders:
    def __init__(self, items):
        self._items = list(items)

    def items(self):
        return list(self._items)

    def get_content_charset(self):
        for name, value in self._items:
            if name.lower() == 'content-type' and 'charset=' in value:
                return value.split('charset=', 1)[1].split(';', 1)[0].strip()
        return None


class FakeResponse:
    def __init__(self, status, body=b'', headers=None):
        self.status = status
        self._body = body
        self.headers = FakeHeaders(headers or [])
        self.closed = False

    def read(self):
        return self._body

    def close(self):
        self.closed = True


# ---- get-content-network-fetch ----------------------------------------------

def test_fetch_returns_status_body_headers():
    response = FakeResponse(
        200,
        b'ok',
        [('Content-Type', 'text/plain; charset=utf-8'), ('X-A', '1')],
    )
    with mock.patch(
        'src.cmdlets.get_content_network_fetch.urlopen',
        return_value=response,
    ) as urlopen_mock:
        result = _fetch('https://cdn.example.com/a.png')
        assert result == {
            'status': 200,
            'body': 'ok',
            'headers': {'Content-Type': 'text/plain; charset=utf-8', 'X-A': '1'},
        }
        assert urlopen_mock.call_args.kwargs['timeout'] == 30  # default timeout


def test_fetch_default_method_is_get():
    with mock.patch(
        'src.cmdlets.get_content_network_fetch.urlopen',
        return_value=FakeResponse(200, b''),
    ) as urlopen_mock:
        _fetch('https://cdn.example.com/a.png')
    request = urlopen_mock.call_args.args[0]
    assert request.get_method() == 'GET'


def test_fetch_uppercases_method_and_allows_head():
    with mock.patch(
        'src.cmdlets.get_content_network_fetch.urlopen',
        return_value=FakeResponse(200, b''),
    ) as urlopen_mock:
        _fetch('https://cdn.example.com/a.png', {'method': 'head'})
    assert urlopen_mock.call_args.args[0].get_method() == 'HEAD'


def test_fetch_read_only_blocks_non_read_only_methods():
    with mock.patch('src.cmdlets.get_content_network_fetch.urlopen') as urlopen_mock:
        with pytest.raises(ValueError):
            _fetch('https://cdn.example.com/a.png', {'method': 'POST'})
        with pytest.raises(ValueError):
            _fetch('https://cdn.example.com/a.png', {'method': 'PUT'})
    urlopen_mock.assert_not_called()


def test_fetch_read_only_false_allows_any_method():
    with mock.patch(
        'src.cmdlets.get_content_network_fetch.urlopen',
        return_value=FakeResponse(201, b''),
    ) as urlopen_mock:
        result = _fetch(
            'https://cdn.example.com/a.png',
            {'method': 'POST', 'read_only': False},
        )
    assert result['status'] == 201
    assert urlopen_mock.call_args.args[0].get_method() == 'POST'


def test_fetch_rejects_non_http_scheme():
    with mock.patch('src.cmdlets.get_content_network_fetch.urlopen') as urlopen_mock:
        with pytest.raises(ValueError):
            _fetch('file:///etc/passwd')
    urlopen_mock.assert_not_called()


def test_fetch_rejects_non_text_value():
    with pytest.raises(TypeError):
        _fetch(123)


def test_fetch_rejects_empty_url():
    with pytest.raises(ValueError):
        _fetch('   ')


def test_fetch_handles_http_error_as_a_result():
    headers = mock.Mock()
    headers.items.return_value = []
    headers.get_content_charset.return_value = None
    error = HTTPError(
        'https://cdn.example.com/missing.png',
        404,
        'Not Found',
        headers,
        io.BytesIO(b'not found'),
    )
    with mock.patch(
        'src.cmdlets.get_content_network_fetch.urlopen',
        side_effect=error,
    ):
        result = _fetch('https://cdn.example.com/missing.png')
    assert result == {'status': 404, 'body': 'not found', 'headers': {}}


def test_fetch_raises_readable_error_on_connection_error():
    with mock.patch(
        'src.cmdlets.get_content_network_fetch.urlopen',
        side_effect=URLError('boom'),
    ):
        with pytest.raises(ValueError) as exc_info:
            _fetch('https://cdn.example.com/a.png')
    assert 'cannot fetch' in str(exc_info.value)
    assert exc_info.value.__cause__ is not None


def test_fetch_decodes_body_with_declared_charset():
    response = FakeResponse(
        200,
        'café'.encode('latin-1'),
        [('Content-Type', 'text/plain; charset=latin-1')],
    )
    with mock.patch(
        'src.cmdlets.get_content_network_fetch.urlopen',
        return_value=response,
    ):
        result = _fetch('https://cdn.example.com/a.png')
    assert result['body'] == 'café'


def test_fetch_joins_repeated_headers():
    response = FakeResponse(
        200,
        b'',
        [('Set-Cookie', 'a=1'), ('Set-Cookie', 'b=2')],
    )
    with mock.patch(
        'src.cmdlets.get_content_network_fetch.urlopen',
        return_value=response,
    ):
        result = _fetch('https://cdn.example.com/a.png')
    assert result['headers'] == {'Set-Cookie': 'a=1, b=2'}


def test_fetch_rejects_invalid_timeout():
    with mock.patch('src.cmdlets.get_content_network_fetch.urlopen') as urlopen_mock:
        with pytest.raises(ValueError):
            _fetch('https://cdn.example.com/a.png', {'timeout': 'abc'})
        with pytest.raises(ValueError):
            _fetch('https://cdn.example.com/a.png', {'timeout': 0})
    urlopen_mock.assert_not_called()


# ---- validate-network-request-result ----------------------------------------

def test_validate_true_for_2xx():
    for status in (200, 201, 204, 299):
        assert _validate({'status': status, 'body': '', 'headers': {}}) is True


def test_validate_false_for_non_2xx():
    for status in (199, 300, 301, 404, 500):
        assert _validate({'status': status, 'body': '', 'headers': {}}) is False


def test_validate_rejects_non_block():
    for value in (None, 200, 'ok', [200]):
        with pytest.raises(TypeError):
            _validate(value)


def test_validate_rejects_missing_fields():
    with pytest.raises(ValueError):
        _validate({'status': 200})


def test_validate_rejects_non_integer_status():
    with pytest.raises(TypeError):
        _validate({'status': '200', 'body': '', 'headers': {}})


def test_validate_rejects_boolean_status():
    with pytest.raises(TypeError):
        _validate({'status': True, 'body': '', 'headers': {}})


def test_validate_accepts_fetch_output():
    response = FakeResponse(200, b'ok', [('X-A', '1')])
    with mock.patch(
        'src.cmdlets.get_content_network_fetch.urlopen',
        return_value=response,
    ):
        fetched = _fetch('https://cdn.example.com/a.png')
    assert _validate(fetched) is True

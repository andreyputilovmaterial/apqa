"""Tests for the `get-content-msmarkitdown` source reader.

The real MarkItDown conversion is not exercised here (it is an optional
dependency and may not be installed), so these tests inject a fake loader to
cover the cmdlet's own wiring: resolving the path, delegating to MarkItDown, and
returning the extracted text.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from src.cmdlets import cmdlets
from src.cmdlets import get_content_msmarkitdown


class _FakeResult:
    def __init__(self, text):
        self.text_content = text


class _FakeMarkItDown:
    def __init__(self, result):
        self._result = result
        self.called_with = None

    def convert(self, source):
        self.called_with = source
        return self._result


def _read(args):
    return cmdlets.get('get-content-msmarkitdown')(None, args)


def test_returns_text_and_passes_resolved_path(monkeypatch):
    fake = _FakeMarkItDown(_FakeResult('converted markdown'))
    monkeypatch.setattr(
        get_content_msmarkitdown, '_load_markitdown', lambda: lambda: fake,
    )
    result = _read({'path': 'sample.docx'})
    assert result == 'converted markdown'
    assert fake.called_with == str(Path('sample.docx').expanduser().resolve())


def test_missing_path_raises(monkeypatch):
    monkeypatch.setattr(get_content_msmarkitdown, '_load_markitdown', lambda: object)
    with pytest.raises(ValueError, match='get-content-msmarkitdown'):
        _read({})


def test_no_matching_converter_raises_readable_error(monkeypatch):
    monkeypatch.setattr(
        get_content_msmarkitdown, '_load_markitdown',
        lambda: lambda: _FakeMarkItDown(None),
    )
    with pytest.raises(ValueError, match='cannot convert'):
        _read({'path': 'unsupported.bin'})


def test_metadata_has_only_path_arg():
    args = cmdlets.describe('get-content-msmarkitdown')['args']
    assert [a['name'] for a in args] == ['path']

"""Tests for the `get-content-text` source reader and its `get-content` proxy."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from src.cmdlets import cmdlets


def _read(name, args):
    return cmdlets.get(name)(None, args)


def test_reads_utf8_file(tmp_path):
    file = tmp_path / 'notes.txt'
    file.write_text('hello\nworld\n', encoding='utf-8')
    assert _read('get-content-text', {'path': str(file)}) == 'hello\nworld\n'


def test_default_encoding_is_utf8(tmp_path):
    file = tmp_path / 'unicode.txt'
    file.write_text('naïve', encoding='utf-8')
    assert _read('get-content-text', {'path': str(file)}) == 'naïve'


def test_reads_with_declared_encoding(tmp_path):
    file = tmp_path / 'latin.txt'
    file.write_text('café', encoding='latin-1')
    assert _read('get-content-text', {'path': str(file), 'encoding': 'latin-1'}) == 'café'


def test_missing_path_raises():
    with pytest.raises(ValueError, match='get-content-text'):
        _read('get-content-text', {})


def test_file_not_found_raises():
    with pytest.raises(FileNotFoundError):
        _read('get-content-text', {'path': '/does/not/exist.txt'})


def test_undecodable_bytes_raise_readable_error(tmp_path):
    file = tmp_path / 'bad.bin'
    file.write_bytes(b'\xff\xfe')
    with pytest.raises(ValueError, match='get-content-text'):
        _read('get-content-text', {'path': str(file)})


def test_get_content_proxy_reads_file(tmp_path):
    file = tmp_path / 'notes.txt'
    file.write_text('same\n', encoding='utf-8')
    assert _read('get-content', {'path': str(file)}) == 'same\n'


def test_get_content_proxy_shares_encoding_arg(tmp_path):
    file = tmp_path / 'latin.txt'
    file.write_text('café', encoding='latin-1')
    assert _read('get-content', {'path': str(file), 'encoding': 'latin-1'}) == 'café'


def test_get_content_proxy_missing_path_raises():
    with pytest.raises(ValueError):
        _read('get-content', {})

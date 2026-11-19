"""Tests for the get-filesystem-obj-info source reader."""

import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from src.cmdlets import cmdlets
from src.cmdlets.sysmissing import sysmissing


def _call(args):
    return cmdlets.get('get-filesystem-obj-info')(None, args)


def test_returns_block_for_existing_file(tmp_path):
    path = tmp_path / 'hello.txt'
    path.write_text('hello', encoding='utf-8')

    info = _call({'path': str(path)})

    assert isinstance(info, dict)
    assert info['type'] == 'file'
    assert info['size'] == 5
    assert isinstance(info['mtime'].value, datetime)
    assert isinstance(info['ctime'].value, datetime)


def test_timestamps_are_timezone_aware_utc(tmp_path):
    path = tmp_path / 'hello.txt'
    path.write_text('hello', encoding='utf-8')

    info = _call({'path': str(path)})

    for field in ('mtime', 'ctime'):
        dt = info[field].value
        assert dt.tzinfo is not None
        assert dt.utcoffset().total_seconds() == 0


def test_type_is_directory_for_directory(tmp_path):
    info = _call({'path': str(tmp_path)})
    assert info['type'] == 'directory'


def test_size_matches_stat(tmp_path):
    path = tmp_path / 'data.bin'
    payload = b'x' * 1024
    path.write_bytes(payload)

    info = _call({'path': str(path)})
    assert info['size'] == len(payload)


def test_birthtime_present_iff_platform_supports(tmp_path):
    path = tmp_path / 'hello.txt'
    path.write_text('hello', encoding='utf-8')

    supported = getattr(path.stat(), 'st_birthtime', None) is not None

    info = _call({'path': str(path)})
    if supported:
        assert isinstance(info['birthtime'].value, datetime)
    else:
        assert info['birthtime'] is sysmissing


def test_birthtime_maps_one_to_one(tmp_path):
    path = tmp_path / 'hello.txt'
    path.write_text('hello', encoding='utf-8')

    raw = getattr(path.stat(), 'st_birthtime', None)
    info = _call({'path': str(path)})

    if raw is None:
        assert info['birthtime'] is sysmissing
    else:
        assert info['birthtime'] == datetime.fromtimestamp(raw, tz=timezone.utc)


def test_returns_sysmissing_for_missing_path(tmp_path):
    missing = tmp_path / 'does-not-exist'
    assert _call({'path': str(missing)}) is sysmissing


def test_requires_path_arg():
    with pytest.raises(ValueError):
        _call({})

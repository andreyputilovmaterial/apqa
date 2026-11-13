"""Resource-path normalization policy for the DB processors.

See ``.clinerules/07-resource-paths.md``. Only physical-file resources
(yaml/sqlite) are resolved to an absolute path, and this happens exactly once,
inside the physical-file DB processor's ``__init__`` — the only place that knows
the resource is a filesystem path. Non-file resource addresses (e.g.
``oledb://``) are detected as such and never resolved.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from src.db_processors import DBFile
from src.db_processors.detect_type import detect_type


def test_detect_type_distinguishes_physical_files_from_resource_addresses():
    assert detect_type('projects.yaml') == 'yaml'
    assert detect_type('projects.sqlite3') == 'sqlite'
    assert detect_type('oledb://server/database') == 'oledb'


def test_yaml_resolves_relative_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'sub').mkdir()
    (tmp_path / 'sub' / 'projects.yaml').write_text('rules: []\n', encoding='utf-8')

    relative = Path('sub') / 'projects.yaml'
    dbfile = DBFile(str(relative))
    assert dbfile.resource_path == relative.resolve()


def test_sqlite_resolves_relative_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    relative = Path('projects.sqlite3')
    DBFile.init_storage(relative)

    dbfile = DBFile(str(relative))
    assert dbfile.resource_path == relative.resolve()


def test_physical_file_processor_init_runs_once(tmp_path):
    """The resource path must be resolved exactly once, not twice."""
    from src.db_processors.yaml import DBFileYaml

    db_file = tmp_path / 'projects.yaml'
    db_file.write_text('rules: []\n', encoding='utf-8')

    calls = []
    original_init = DBFileYaml.__init__

    def counting_init(self, resource_path):
        calls.append(resource_path)
        original_init(self, resource_path)

    DBFileYaml.__init__ = counting_init
    try:
        DBFile(str(db_file))
    finally:
        DBFileYaml.__init__ = original_init

    assert len(calls) == 1


def test_non_file_resource_address_is_not_resolved():
    # No oledb processor is registered, so opening one must fail at detection
    # rather than treating it as a filesystem path and resolving it.
    with pytest.raises(NotImplementedError):
        DBFile('oledb://server/database')


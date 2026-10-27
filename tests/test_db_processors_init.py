"""Creating a fresh QC-rules storage via the registry router.

`DBFile.init_storage` is the single entry point used by `--program init`. It
derives the storage format from the path (via `detect_type`) unless one is
passed explicitly, then routes to the registered processor's `_init_storage`.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from src.db_processors import DBFile, DBFileSqlite, DBFileYaml


def test_init_yaml_creates_empty_storage(tmp_path):
    db_file = tmp_path / "projects.yaml"
    created = DBFile.init_storage(db_file)

    assert created == db_file.resolve()
    assert db_file.is_file()

    dbfile = DBFile(str(db_file))
    assert len(dbfile) == 0
    assert dbfile.list_groups() == []


def test_init_sqlite_creates_empty_storage(tmp_path):
    db_file = tmp_path / "projects.sqlite3"
    created = DBFile.init_storage(db_file)

    assert created == db_file.resolve()
    assert db_file.is_file()

    dbfile = DBFile(str(db_file))
    assert len(dbfile) == 0
    assert dbfile.list_groups() == []


def test_init_explicit_format_overrides_extension(tmp_path):
    db_file = tmp_path / "projects.dat"
    created = DBFile.init_storage(db_file, "yaml")

    assert created == db_file.resolve()
    # A `.dat` path cannot be auto-detected on open, so open via the concrete
    # processor to prove the explicit format was honored.
    dbfile = DBFileYaml(str(db_file))
    assert len(dbfile) == 0


def test_init_explicit_sqlite_format(tmp_path):
    db_file = tmp_path / "projects.db"
    created = DBFile.init_storage(db_file, "sqlite")

    assert created == db_file.resolve()
    dbfile = DBFileSqlite(str(db_file))
    assert len(dbfile) == 0


def test_init_existing_file_raises(tmp_path):
    db_file = tmp_path / "projects.yaml"
    db_file.write_text("already: here", encoding="utf-8")

    with pytest.raises(FileExistsError):
        DBFile.init_storage(db_file)


def test_init_unrecognized_extension_raises(tmp_path):
    db_file = tmp_path / "projects.txt"

    with pytest.raises(NotImplementedError):
        DBFile.init_storage(db_file)


def test_init_unregistered_format_raises(tmp_path):
    db_file = tmp_path / "projects.yaml"

    with pytest.raises(NotImplementedError):
        DBFile.init_storage(db_file, "nope")


def test_main_init_program_creates_and_reports(tmp_path, capsys):
    from src.main_init_program import main

    db_file = tmp_path / "projects.yaml"
    created = main(["--db-file", str(db_file)])

    captured = capsys.readouterr()
    assert created == db_file.resolve()
    assert db_file.is_file()
    assert "created" in captured.out
    assert "db_file" in captured.out


def test_main_init_program_explicit_format(tmp_path, capsys):
    from src.main_init_program import main

    db_file = tmp_path / "projects.dat"
    main(["--db-file", str(db_file), "--db-format", "yaml"])

    dbfile = DBFileYaml(str(db_file))
    assert len(dbfile) == 0

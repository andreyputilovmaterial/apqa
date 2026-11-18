"""HTTP DB processor: client + standalone fixture server, end-to-end.

The server under test is the repo-root ``http_db_server.py`` fixture, which is
independent of ``src`` — so these tests exercise the documented wire contract
across two implementations (client vs server), exactly what "the design is
scalable" means.
"""

import base64
import json
import sys
import threading
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from src.db_processors import DBFile
from src.db_processors.http.dbfile import parse_http_resource
from src.db_processors.rule_base import Rule

import http_db_server


def _credentialed(url):
    return url.replace("http://", "http://user:pass@", 1)


@pytest.fixture
def server():
    document = http_db_server.HttpDbDocument(http_db_server.empty_document())
    requests_log = []
    srv = http_db_server.make_server(
        "127.0.0.1", 0, document=document, username="user", password="pass", requests_log=requests_log
    )
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    host, port = srv.server_address
    try:
        yield f"http://{host}:{port}", document, requests_log
    finally:
        srv.shutdown()
        srv.server_close()
        thread.join(timeout=5)


def _run_server(document, username=None, password=None):
    srv = http_db_server.make_server(
        "127.0.0.1", 0, document=document, username=username, password=password
    )
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    host, port = srv.server_address
    return srv, thread, f"http://{host}:{port}"


# ---- sanitizing / resource path -------------------------------------------

def test_parse_http_resource_sanitizes_credentials():
    clean, auth = parse_http_resource("http://user:pass@localhost:4001")
    assert clean == "http://localhost:4001"
    assert auth == "Basic " + base64.b64encode(b"user:pass").decode("ascii")
    assert "user" not in clean and "pass" not in clean


def test_parse_http_resource_without_credentials():
    clean, auth = parse_http_resource("http://localhost:4001")
    assert clean == "http://localhost:4001"
    assert auth is None


def test_parse_http_resource_rejects_non_http():
    with pytest.raises(ValueError):
        parse_http_resource("oledb://server/db")


def test_resource_path_is_clean_and_not_resolved(server):
    url, _doc, _log = server
    dbfile = DBFile(_credentialed(url))
    assert dbfile.resource_path == url
    assert "user" not in dbfile.resource_path and "pass" not in dbfile.resource_path
    assert dbfile.resource_path != str(Path(dbfile.resource_path).resolve())


def test_auth_header_sent_on_open_and_save(server):
    url, _doc, log = server
    dbfile = DBFile(_credentialed(url))
    expected = "Basic " + base64.b64encode(b"user:pass").decode("ascii")
    assert log[0]["method"] == "GET"
    assert log[0]["auth"] == expected

    dbfile.update_project(name="Demo")
    dbfile.save()
    put = [r for r in log if r["method"] == "PUT"][-1]
    assert put["auth"] == expected


# ---- served from backend --------------------------------------------------

def test_served_project_path_is_clean(server):
    from src.frontend.endpoints_qcrules.project import handle_project_crud
    from src.webserver_engine.webserve.src.common_defs import WebResponse

    url, _doc, _log = server
    dbfile = DBFile(_credentialed(url))

    class FakeRequest:
        command = "GET"
        path = "/qc/project"
        headers = {}
        request_body = None

        def __init__(self):
            self.request_body = self

        def read(self):
            return b""

    config = {"iface": {"WebResponse": WebResponse, "db_file": dbfile}}
    resp = handle_project_crud(FakeRequest(), config, added_data='/qc/project')
    data = json.loads(resp.body)
    assert data["path"] == url
    assert "user" not in data["path"] and "pass" not in data["path"]


# ---- CRUD round-trip ------------------------------------------------------

def test_crud_roundtrip(server):
    url, _doc, _log = server
    dbfile = DBFile(_credentialed(url))

    dbfile.add_rule({"name": "wave counts", "op": "cmp-eq"})
    dbfile.add_group({"name": "Data"})
    dbfile.update_project(name="Demo")
    dbfile.save()

    reloaded = DBFile(_credentialed(url))
    assert reloaded.get_project().name == "Demo"
    rules = reloaded.list_rules()
    assert [r.name for r in rules] == ["wave counts"]
    assert all(isinstance(r, Rule) for r in rules)
    assert [g.name for g in reloaded.list_groups()] == ["Data"]


def test_get_rule_missing(server):
    url, _doc, _log = server
    dbfile = DBFile(_credentialed(url))
    with pytest.raises(KeyError):
        dbfile.get_rule("nope")
    assert not dbfile.has_rule("nope")


# ---- 404 / error handling -------------------------------------------------

def test_404_opens_empty():
    document = http_db_server.HttpDbDocument(None)
    srv, thread, url = _run_server(document)
    try:
        dbfile = DBFile(url)
        assert len(dbfile) == 0
        assert dbfile.list_groups() == []
    finally:
        srv.shutdown()
        srv.server_close()
        thread.join(timeout=5)


def test_open_error_maps_to_valueerror(server, monkeypatch):
    import src.db_processors.http.dbfile as http_mod
    url, _doc, _log = server
    monkeypatch.setattr(http_mod, "_http_request", lambda *a, **k: (500, {"error": "boom"}))
    with pytest.raises(ValueError):
        DBFile(_credentialed(url))


def test_save_error_maps_to_valueerror(server, monkeypatch):
    import src.db_processors.http.dbfile as http_mod
    url, _doc, _log = server
    dbfile = DBFile(_credentialed(url))
    monkeypatch.setattr(http_mod, "_http_request", lambda *a, **k: (400, {"error": "rejected"}))
    with pytest.raises(ValueError):
        dbfile.save()


# ---- init storage ---------------------------------------------------------

def test_init_storage_creates_remote():
    document = http_db_server.HttpDbDocument(None)
    srv, thread, url = _run_server(document)
    try:
        created = DBFile.init_storage(url)
        assert created == url
        assert document.get() == http_db_server.empty_document()
    finally:
        srv.shutdown()
        srv.server_close()
        thread.join(timeout=5)


def test_init_storage_existing_raises(server):
    url, _doc, _log = server
    with pytest.raises(FileExistsError):
        DBFile.init_storage(_credentialed(url))

#!/usr/bin/env python3
"""Standalone dev fixture: a minimal HTTP database for the APQA rules store.

Serves the single-document wire protocol spoken by ``DBFileHttp``
(``src/db_processors/http/dbfile.py``):

    GET <url>  -> 200 + {"project": {...}, "groups": [...], "rules": [...]}
                  (404 when the document has not been created yet)
    PUT <url>  with that JSON document -> store it (200), or 400 on bad input

The whole database is a single JSON document (the same shape as the YAML file),
so this server is intentionally independent of the app's code: it only shares
the documented wire contract with the client. Run it and point the app at it:

    python http_db_server.py --port 4001 --username user --password pass

    python -m src.launcher --program ui --db-file http://user:pass@localhost:4001

Optional Basic auth is compared against the ``Authorization`` header. ``--seed``
loads the initial document from any DBFile-supported file (sqlite/yaml) by
reusing ``src.db_processors.DBFile``; ``--save-to`` persists every accepted PUT
to a YAML file so edits made in the UI can be inspected.

NOTE: credentials in ``--db-file`` (``user:pass@``) still appear in the process
command line / shell history; see ``docs/roadmap.md``.
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 4001


def empty_document():
    return {"project": {"name": "", "comment": "", "meta": {}}, "groups": [], "rules": []}


class HttpDbDocument:
    """In-memory document plus optional YAML persistence."""

    def __init__(self, document=None, save_to=None):
        self.document = document
        self.save_to = save_to

    def get(self):
        return self.document

    def put(self, document):
        self.document = document
        if self.save_to:
            self._write(document)
        return document

    def _write(self, document):
        import yaml
        path = Path(self.save_to)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(document, f, sort_keys=False)


def make_http_db_handler(document, username=None, password=None, requests_log=None):
    """Build a request handler serving ``document`` (an ``HttpDbDocument``).

    ``requests_log``, when given, is a list that each handled request appends a
    dict to (method, path, auth, status), so tests can assert on the
    Authorization header and method.
    """
    expected_auth = None
    if username is not None or password is not None:
        token = base64.b64encode(f'{username or ""}:{password or ""}'.encode("utf-8")).decode("ascii")
        expected_auth = f"Basic {token}"

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):  # noqa: A002
            sys.stderr.write(f"{self.address_string()} - {format % args}\n")

        def _authorized(self):
            if expected_auth is None:
                return True
            return self.headers.get("Authorization") == expected_auth

        def _send_json(self, status, payload):
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _record(self, status):
            if requests_log is not None:
                requests_log.append({
                    "method": self.command,
                    "path": self.path,
                    "auth": self.headers.get("Authorization"),
                    "status": status,
                })

        def do_GET(self):
            if not self._authorized():
                self._record(401)
                return self._send_json(401, {"error": "unauthorized"})
            doc = document.get()
            if doc is None:
                self._record(404)
                return self._send_json(404, {"error": "not found"})
            self._record(200)
            self._send_json(200, doc)

        def do_PUT(self):
            if not self._authorized():
                self._record(401)
                return self._send_json(401, {"error": "unauthorized"})
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b""
            if not raw:
                payload = empty_document()
            else:
                try:
                    payload = json.loads(raw.decode("utf-8"))
                except (ValueError, UnicodeDecodeError):
                    self._record(400)
                    return self._send_json(400, {"error": "invalid JSON body"})
            if not isinstance(payload, dict):
                self._record(400)
                return self._send_json(400, {"error": "body must be a JSON object"})
            document.put(payload)
            self._record(200)
            self._send_json(200, payload)

    return Handler


def make_server(host=DEFAULT_HOST, port=DEFAULT_PORT, document=None, username=None, password=None, requests_log=None):
    handler = make_http_db_handler(document, username, password, requests_log)
    return ThreadingHTTPServer((host, port), handler)


def load_document_from_dbfile(path):
    """Load the JSON document shape from any DBFile-supported file."""
    root = Path(__file__).resolve().parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from src.db_processors import DBFile
    dbfile = DBFile(str(path))
    return {
        "project": dbfile.get_project().to_dict(),
        "groups": [group.to_dict() for group in dbfile.list_groups()],
        "rules": [rule.to_dict() for rule in dbfile.list_rules()],
    }


def build_parser():
    parser = argparse.ArgumentParser(
        prog="http_db_server.py",
        description="Serve the APQA rules database as a single JSON document over HTTP.",
    )
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--seed", help="load the initial document from a DBFile-supported file (sqlite/yaml)")
    parser.add_argument("--save-to", help="persist every accepted PUT to this YAML file")
    parser.add_argument("--username", default=None)
    parser.add_argument("--password", default=None)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if (args.username is None) != (args.password is None):
        build_parser().error("--username and --password must be given together")

    document = load_document_from_dbfile(args.seed) if args.seed else empty_document()
    doc = HttpDbDocument(document=document, save_to=args.save_to)
    server = make_server(
        args.host, args.port, document=doc, username=args.username, password=args.password
    )
    host, port = server.server_address
    address = f"http://{host}:{port}"
    if args.username is not None:
        address = f"http://{args.username}:{args.password}@{host}:{port}"
    print(f"APQA HTTP database fixture listening on {address} (Ctrl-C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

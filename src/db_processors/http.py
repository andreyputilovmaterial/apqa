"""HTTP client to a remote QC-rules database (single-document wire protocol).

The remote server stores the whole database as one JSON document and exposes it
via two verbs::

    GET <url>  -> 200 with {"project": {...}, "groups": [...], "rules": [...]}
                  (404 means "no document yet" and is treated as empty)
    PUT <url>  -> with that same document, to persist it (any 2xx)

The URL *is* the database address (``http://host:port[/path]``). It may carry
credentials in the userinfo part (``http://username:password@host:port``); those
are parsed into an ``Authorization: Basic ...`` header and the userinfo is
**removed** from the stored ``resource_path``, so credentials never leak into
``config['db_file']``, the page header, or ``GET /qc/project``.

NOTE (accepted trade-off for now): putting credentials in ``--db-file`` still
leaves them visible in the process command line / shell history. We sanitize
them out of everything the app stores and serves, but a future, safer mechanism
(an env var, a token file, or an interactive prompt) is tracked in
``docs/roadmap.md``.
"""

import base64
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen

from .dbfile_base import DBFile as DBFileBase
from .document_base import DBFileDocument


_DEFAULT_TIMEOUT = 30
_EMPTY_DOCUMENT = {
    'project': {'name': '', 'comment': '', 'meta': {}},
    'groups': [],
    'rules': [],
}


def parse_http_resource(resource_path):
    """Return ``(clean_url, auth_header)`` for an ``http(s)://`` resource address.

    ``clean_url`` is the address with any ``user:pass@`` userinfo removed (and
    query/fragment dropped), so the credentials never leak into stored or served
    paths. ``auth_header`` is ``None`` or an ``Authorization: Basic ...`` value
    built from the userinfo.
    """
    text = f'{resource_path}'
    parts = urlsplit(text)
    scheme = (parts.scheme or '').lower()
    if scheme not in ('http', 'https'):
        raise ValueError(
            f'db file: http resource must use http:// or https://: {text!r}'
        )

    netloc = parts.netloc
    auth_header = None
    if '@' in netloc:
        userinfo, netloc = netloc.rsplit('@', 1)
        username, _, password = userinfo.partition(':')
        token = base64.b64encode(f'{username}:{password}'.encode('utf-8')).decode('ascii')
        auth_header = f'Basic {token}'

    if not netloc:
        raise ValueError(f'db file: http resource has no host: {text!r}')

    clean_url = urlunsplit((scheme, netloc, parts.path, '', ''))
    return clean_url, auth_header


def _response_status(response):
    for attr in ('status', 'code'):
        raw = getattr(response, attr, None)
        if raw is None:
            continue
        try:
            return int(raw)
        except (TypeError, ValueError):
            continue
    return 0


def _parse_json(body):
    if not body:
        return None
    try:
        return json.loads(body.decode('utf-8'))
    except (ValueError, UnicodeDecodeError):
        return None


def _http_request(url, method, auth_header, payload=None, timeout=_DEFAULT_TIMEOUT):
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    if auth_header:
        headers['Authorization'] = auth_header

    request = Request(url, data=data, headers=headers, method=method)
    try:
        response = urlopen(request, timeout=timeout)
    except HTTPError as error:
        response = error
    except URLError as error:
        raise ValueError(f'db file: cannot reach http resource {url!r}') from error

    try:
        status = _response_status(response)
        body = response.read()
    finally:
        close = getattr(response, 'close', None)
        if callable(close):
            close()

    return status, _parse_json(body)


def _http_error(url, status, data):
    message = (data or {}).get('error') if isinstance(data, dict) else None
    if message:
        return ValueError(f'db file: http resource {url!r} returned HTTP {status}: {message}')
    return ValueError(f'db file: http resource {url!r} returned HTTP {status}')


@DBFileBase.register('http')
@DBFileBase.register('https')
class DBFileHttp(DBFileDocument):
    """Remote QC-rules database accessed over HTTP as a single JSON document.

    Like the YAML backend, the whole database is kept in memory and the document
    is fetched on open and pushed on :meth:`save`. All CRUD is inherited from
    :class:`~.document_base.DBFileDocument`; only the transport (GET/PUT) and the
    resource-address handling live here.
    """

    def __init__(self, resource_path):
        clean_url, auth_header = parse_http_resource(resource_path)
        super().__init__(clean_url)
        self._auth_header = auth_header
        self._document_url = clean_url
        self._read()

    @classmethod
    def _init_storage(cls, resource_path):
        clean_url, auth_header = parse_http_resource(resource_path)
        status, _data = _http_request(clean_url, 'GET', auth_header)
        if status != 404:
            raise FileExistsError(f'db file: already exists: {clean_url}')
        status, data = _http_request(clean_url, 'PUT', auth_header, _EMPTY_DOCUMENT)
        if status >= 400:
            raise _http_error(clean_url, status, data)
        return clean_url

    def _read(self):
        status, data = _http_request(self._document_url, 'GET', self._auth_header)
        if status == 404:
            self._read_document(_EMPTY_DOCUMENT)
            return
        if status >= 400:
            raise _http_error(self._document_url, status, data)
        self._read_document(data or _EMPTY_DOCUMENT)

    def save(self):
        status, data = _http_request(
            self._document_url, 'PUT', self._auth_header, self._to_document()
        )
        if status >= 400:
            raise _http_error(self._document_url, status, data)

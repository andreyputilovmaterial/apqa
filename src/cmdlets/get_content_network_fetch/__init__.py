"""`get-content-network-fetch` — fetch a URL and return a block with ``status``,
``body``, and ``headers``.

The URL is taken from the **piped value** (a text value), so this cmdlet is a
*processor*: it follows a source that produces a URL (for example ``literal``
with a URL value, or — once the ``select-property`` middle cmdlet exists — a URL
read from an Excel/CSV column).

Args (stored named mapping):

    method      HTTP method, default ``"GET"``. Any method string is accepted
                (``HEAD``, ``GET``, ``POST``, ``PUT``, …).
    read_only   bool, default ``true``. When true, only ``GET``/``HEAD`` are
                allowed and any other method raises; set false to allow all
                methods.
    timeout     number, default ``30`` — request timeout in seconds.

The result is a block with exactly three fields:

    status      integer HTTP status code.
    body        response body decoded as text (empty for ``HEAD``).
    headers     response headers as a block keyed by header name (repeated
                header values are joined with ``", "``).

Only ``http``/``https`` URLs are accepted (a minimal safety guard against
``file://`` and other schemes; a full permission model is tracked in
``docs/roadmap.md``). ``urllib.request`` is part of the Python standard library.
"""

from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from ..registry import cmdlets
from ..value_types import Block, PipeValue

_DEFAULT_METHOD = 'GET'
_DEFAULT_TIMEOUT = 30
_READ_ONLY_METHODS = ('GET', 'HEAD')
_ALLOWED_SCHEMES = ('http', 'https')


@cmdlets.register(
    'get-content-network-fetch',
    kind='processor',
    help='Fetch a URL and return a block with status, body, and headers.',
    args=[
        {
            'name': 'method',
            'type': 'text',
            'required': False,
            'default': _DEFAULT_METHOD,
            'description': 'HTTP method (GET, HEAD, POST, PUT, ...).',
        },
        {
            'name': 'read_only',
            'type': 'boolean',
            'required': False,
            'default': True,
            'description': 'Require a read-only method (GET or HEAD); raise otherwise.',
        },
        {
            'name': 'timeout',
            'type': 'number',
            'required': False,
            'default': _DEFAULT_TIMEOUT,
            'description': 'Request timeout in seconds.',
        },
    ],
)
def get_content_network_fetch(value: PipeValue, args: dict) -> Block:
    """Fetch ``value`` (a URL) and return a ``{status, body, headers}`` block."""
    if not isinstance(value, str):
        raise TypeError(
            'get-content-network-fetch: expected a URL as text, got '
            f'{type(value).__name__}'
        )
    url = value.strip()
    if url == '':
        raise ValueError('get-content-network-fetch: URL must not be empty')

    _check_scheme(url)

    method = _normalize_method(args.get('method'))
    read_only = bool(args.get('read_only', True))
    if read_only and method not in _READ_ONLY_METHODS:
        raise ValueError(
            "get-content-network-fetch: method must be 'GET' or 'HEAD' when "
            f"'read_only' is true (got {method!r})"
        )

    timeout = _coerce_timeout(args.get('timeout', _DEFAULT_TIMEOUT))

    request = Request(url, method=method)
    try:
        response = urlopen(request, timeout=timeout)
    except HTTPError as error:
        # A non-2xx response is still a valid result for this cmdlet: report it
        # as a block rather than raising, so a rule can assert on the status.
        response = error
    except URLError as error:
        raise ValueError(
            f'get-content-network-fetch: cannot fetch {url!r}'
        ) from error

    try:
        status = _response_status(response)
        body = _decode_body(response.read(), response.headers.get_content_charset())
        headers = _headers_block(response.headers)
    finally:
        close = getattr(response, 'close', None)
        if callable(close):
            close()

    return {'status': status, 'body': body, 'headers': headers}


def _normalize_method(method):
    method = method if method is not None else _DEFAULT_METHOD
    method = str(method).strip().upper()
    return method or _DEFAULT_METHOD


def _check_scheme(url):
    scheme = urlparse(url).scheme.lower()
    if scheme not in _ALLOWED_SCHEMES:
        raise ValueError(
            'get-content-network-fetch: only http/https URLs are supported '
            f'(got {url!r})'
        )


def _coerce_timeout(value):
    if value is None:
        return _DEFAULT_TIMEOUT
    try:
        timeout = float(value)
    except (TypeError, ValueError):
        raise ValueError(
            "get-content-network-fetch: 'timeout' must be a number, got "
            f'{value!r}'
        ) from None
    if timeout <= 0:
        raise ValueError('get-content-network-fetch: timeout must be positive')
    return timeout


def _response_status(response):
    for attr in ('status', 'code'):
        raw = getattr(response, attr, None)
        if raw is None:
            continue
        try:
            return int(raw)
        except (TypeError, ValueError):
            continue
    raise ValueError(
        'get-content-network-fetch: could not determine HTTP status code'
    )


def _decode_body(data, charset):
    if not data:
        return ''
    encoding = charset or 'utf-8'
    try:
        return data.decode(encoding)
    except (UnicodeDecodeError, LookupError):
        return data.decode('utf-8', errors='replace')


def _headers_block(message):
    block = {}
    for name, value in message.items():
        if name in block:
            block[name] = f'{block[name]}, {value}'
        else:
            block[name] = value
    return block

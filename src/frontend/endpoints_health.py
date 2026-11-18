
from urllib.parse import urlparse
import json

from .common_functions import path_relative_to


# net_request_handler is derived from BaseHTTPRequestHandler (python's http.server).
def handle_health(net_request_handler, config: dict, added_data=None):
    """Liveness probe, dispatched from the ``/health`` route.

    Requests (``<mount>`` = the route registered in ``src/endpoints.py`` and
    passed via ``added_data``; nothing in the path, query string, or body):

    - ``GET <mount>`` / ``HEAD <mount>`` -> ``{"status": "ok"}`` (self-contained,
      does not touch the project DB; the webserver suppresses the HEAD body).
    """

    WebResponse = config.get('iface').get('WebResponse')

    method = net_request_handler.command
    path_parsed = f'{urlparse(net_request_handler.path).path}'

    if path_relative_to(path_parsed, added_data) == '':
        if method in ('GET',):
            return WebResponse(
                status_code=200,
                content_type='application/json',
                body=json.dumps({'status': 'ok'}),
                headers=[],
            )
        elif method in ('HEAD',):
            return WebResponse(
                status_code=200,
                content_type='application/json',
                body=None,
                headers=[],
            )

    return WebResponse(
            status_code=405,
            content_type='application/json',
            body=json.dumps({'error': f'renderer for {method} {path_parsed} is not recognized'}),
            headers=[],
        )

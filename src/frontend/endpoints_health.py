
from urllib.parse import urlparse
import json


# Liveness probe for the backend. Responds 200 to HEAD (what the frontend uses
# to detect whether the backend process is still up) and to GET (for humans and
# browsers). It must not depend on the project DB file: this endpoint only
# answers "is the server running". Project identity ("is the backend still
# serving the same project file") is verified separately via GET /qc/project,
# whose `path` field is the absolute path to the project file.
#
# net_request_handler is derived from BaseHTTPRequestHandler (python's
# http.server). The webserver engine already suppresses the response body for
# HEAD requests (it keeps Content-length but skips writing the body), so the
# same renderer serves both GET and HEAD.
def handle_health(net_request_handler, config: dict, added_data=None):

    WebResponse = config.get('iface').get('WebResponse')

    def json_response(status_code, data, headers=None):
        return WebResponse(
            status_code=status_code,
            content_type='application/json',
            body=json.dumps(data),
            headers=headers or [],
        )

    method = net_request_handler.command
    path_parsed = f'{urlparse(net_request_handler.path).path}'

    if path_parsed == '/health':
        if method in ('GET', 'HEAD'):
            return json_response(200, {'status': 'ok'})

    return json_response(405, {'error': f'renderer for {method} {path_parsed} is not recognized'})

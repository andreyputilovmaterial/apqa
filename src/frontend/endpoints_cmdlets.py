
from urllib.parse import urlparse
import json

from .common_functions import JSONEncoder, path_relative_to


# net_request_handler is derived from BaseHTTPRequestHandler (python's http.server).
def handle_cmdlets(net_request_handler, config: dict, added_data=None):
    """Cmdlet/op editor metadata, dispatched from the ``/cmdlets`` route.

    Requests (``<mount>`` = the route registered in ``src/endpoints.py`` and
    passed via ``added_data``; all GET, nothing in the path or query string):

    - ``GET <mount>/metadata`` -> `handle_metadata`: return cmdlet/op editor metadata.

    ``handle_metadata`` delegates to ``config['iface']['get_cmdlet_metadata']``
    (``src/cmdlets/meta.py``).
    """

    WebResponse = config.get('iface').get('WebResponse')

    def json_response(status_code, data, headers=None):
        return WebResponse(
            status_code=status_code,
            content_type='application/json',
            body=json.dumps(data, cls=JSONEncoder),
            headers=headers or [],
        )

    def handle_metadata():
        get_cmdlet_metadata = (config.get('iface') or {}).get('get_cmdlet_metadata')
        if not callable(get_cmdlet_metadata):
            return json_response(404, {'error': 'cmdlet metadata is not available'})
        return json_response(200, get_cmdlet_metadata())

    method = net_request_handler.command
    path_with_query = net_request_handler.path
    path_parsed = f'{urlparse(path_with_query).path}'
    relative = path_relative_to(path_parsed, added_data)

    renderer = None

    if relative == '/metadata' and method == 'GET':
        renderer = handle_metadata

    if renderer is None:
        return json_response(405, {'error': f'renderer for {method} {path_parsed} is not recognized'})
    return renderer()

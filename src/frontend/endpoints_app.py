
from urllib.parse import urlparse
import json

from .common_functions import JSONEncoder, path_relative_to


# net_request_handler is derived from BaseHTTPRequestHandler (python's http.server).
def handle_app(net_request_handler, config: dict, added_data=None):
    """App config / help pages, dispatched from the ``/app`` route.

    Requests (``<mount>`` = the route registered in ``src/endpoints.py`` and
    passed via ``added_data``; all GET, nothing in the path or query string):

    - ``GET <mount>/config`` -> `handle_config`: serialize the app config (sans ``iface``).
    - ``GET <mount>/help-pages`` -> `handle_help_pages`: return the bundled help markdown.

    ``handle_help_pages`` delegates to ``config['iface']['get_help_pages']``
    (``src/main_ui_program.py``).
    """

    WebResponse = config.get('iface').get('WebResponse')

    def json_response(status_code, data, headers=None):
        return WebResponse(
            status_code=status_code,
            content_type='application/json',
            body=json.dumps(data, cls=JSONEncoder),
            headers=headers or [],
        )

    def config_for_transport():
        # `iface` holds callables, classes, and a DBFile handle that are not
        # meant to be serialized to JSON. Drop it, keep everything else (dates
        # are ISO-ified by JSONEncoder).
        result = dict(config)
        result.pop('iface', None)
        return result

    def handle_config():
        return json_response(200, config_for_transport())

    def handle_help_pages():
        get_help_pages = (config.get('iface') or {}).get('get_help_pages')
        if not callable(get_help_pages):
            return json_response(404, {'error': 'help pages are not available'})
        return json_response(200, {'help_pages': get_help_pages()})

    method = net_request_handler.command
    path_with_query = net_request_handler.path
    path_parsed = f'{urlparse(path_with_query).path}'
    relative = path_relative_to(path_parsed, added_data)

    renderer = None

    if relative == '/config' and method == 'GET':
        renderer = handle_config
    elif relative == '/help-pages' and method == 'GET':
        renderer = handle_help_pages

    if renderer is None:
        return json_response(405, {'error': f'renderer for {method} {path_parsed} is not recognized'})
    return renderer()

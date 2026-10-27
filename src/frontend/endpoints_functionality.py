
from urllib.parse import urlparse
import json

from .common_functions import JSONEncoder


# net_request_handler is derived from BaseHTTPRequestHandler (python's http.server).
# All requests under /functionality... arrive here (any HTTP method); method+path
# routing is done below with simple if...elif, following the pattern used in this codebase.
def handle_functionality(net_request_handler, config: dict, added_data=None):

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

    def handle_cmdlet_metadata():
        get_cmdlet_metadata = (config.get('iface') or {}).get('get_cmdlet_metadata')
        if not callable(get_cmdlet_metadata):
            return json_response(404, {'error': 'cmdlet metadata is not available'})
        return json_response(200, get_cmdlet_metadata())

    method = net_request_handler.command
    path_with_query = net_request_handler.path
    path_parsed = f'{urlparse(path_with_query).path}'

    renderer = None

    if path_parsed == '/functionality/config':
        if method == 'GET':
            renderer = handle_config
    elif path_parsed == '/functionality/help-pages':
        if method == 'GET':
            renderer = handle_help_pages
    elif path_parsed == '/functionality/cmdlet-metadata':
        if method == 'GET':
            renderer = handle_cmdlet_metadata

    if renderer is None:
        return json_response(405, {'error': f'renderer for {method} {path_parsed} is not recognized'})
    return renderer()


from urllib.parse import urlparse
import json


# net_request_handler is derived from BaseHTTPRequestHandler (python's http.server).
def handle_functionality(net_request_handler, config: dict, added_data=None):
    """Grab-bag for miscellaneous endpoints that have no clearer home yet.

    Deliberately empty: every request that reaches ``/functionality`` (or below)
    returns ``404``. The route is kept so the namespace stays reserved and
    discoverable instead of being re-invented later; when a new piece of
    functionality doesn't obviously belong to ``/app``, ``/cmdlets``, ``/qc``,
    ``/tests``, or ``/health``, it can be mounted here.
    """

    WebResponse = config.get('iface').get('WebResponse')
    path_parsed = f'{urlparse(net_request_handler.path).path}'

    return WebResponse(
        status_code=404,
        content_type='application/json',
        body=json.dumps({
            'error': f'/functionality is an empty grab-bag: nothing is registered under {path_parsed}',
        }),
        headers=[],
    )

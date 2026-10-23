
from urllib.parse import urlparse
import json

from .common_functions import JSONEncoder


# net_request_handler is derived from BaseHTTPRequestHandler (python's http.server).
# POST /functionality/run-rule runs an *arbitrary* rule passed as JSON. It does
# not address a rule that lives in the rules database (that is the /qcrules...
# namespace), so it deliberately lives under /functionality/ instead.
def handle_rule_run(net_request_handler, config: dict, added_data=None):

    WebResponse = config.get('iface').get('WebResponse')
    run_rule = (config.get('iface') or {}).get('run_rule')

    def json_response(status_code, data, headers=None):
        return WebResponse(
            status_code=status_code,
            content_type='application/json',
            body=json.dumps(data, cls=JSONEncoder),
            headers=headers or [],
        )

    method = net_request_handler.command
    path = f'{urlparse(net_request_handler.path).path}'

    if path != '/functionality/run-rule' or method != 'POST':
        return json_response(
            405, {'error': f'renderer for {method} {path} is not recognized'}
        )

    if not callable(run_rule):
        return json_response(404, {'error': 'rule runner is not available'})

    body = net_request_handler.request_body.read()
    if not body:
        return json_response(400, {'error': 'request body must be a valid JSON object'})

    try:
        payload = json.loads(body)
    except ValueError:
        return json_response(400, {'error': 'request body must be a valid JSON object'})

    if not isinstance(payload, dict):
        return json_response(400, {'error': 'request body must be a JSON object (rule)'})

    try:
        result = run_rule(payload)
    except Exception as e:
        return json_response(400, {'error': f'{e}'})

    return json_response(200, {'result': bool(result)})

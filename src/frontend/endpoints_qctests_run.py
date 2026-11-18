
from urllib.parse import urlparse
import json

from .common_functions import JSONEncoder, path_relative_to


# net_request_handler is derived from BaseHTTPRequestHandler (python's http.server).
def handle_qcrule_run(net_request_handler, config: dict, added_data=None):
    """Run an arbitrary QC rule, dispatched from the ``/tests/run`` route.

    Requests (``<mount>`` = the route registered in ``src/endpoints.py`` and
    passed via ``added_data``; the rule arrives as a JSON request body, nothing
    in the path or query string):

    - ``POST <mount>`` (JSON body: a rule dict) -> `run_rule_with_report` /
      `run_rule`: execute the rule, return ``{result, notes?}``.

    Rule execution is delegated to ``config['iface']['run_rule_with_report']`` /
    ``config['iface']['run_rule']`` (see ``src/rule_runner.py``).
    """

    WebResponse = config.get('iface').get('WebResponse')
    run_rule = (config.get('iface') or {}).get('run_rule')
    run_rule_with_report = (config.get('iface') or {}).get('run_rule_with_report')

    def json_response(status_code, data, headers=None):
        return WebResponse(
            status_code=status_code,
            content_type='application/json',
            body=json.dumps(data, cls=JSONEncoder),
            headers=headers or [],
        )

    method = net_request_handler.command
    path = f'{urlparse(net_request_handler.path).path}'

    if path_relative_to(path, added_data) != '' or method != 'POST':
        return json_response(
            405, {'error': f'renderer for {method} {path} is not recognized'}
        )

    if not callable(run_rule) and not callable(run_rule_with_report):
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
        if callable(run_rule_with_report):
            result, notes = run_rule_with_report(payload)
            data = {'result': bool(result)}
            if notes:
                data['notes'] = notes
            return json_response(200, data)
        result = run_rule(payload)
    except Exception as e:
        return json_response(400, {'error': f'{e}'})

    return json_response(200, {'result': bool(result)})


from urllib.parse import urlparse
import json

from .common_functions import JSONEncoder


# net_request_handler is derived from BaseHTTPRequestHandler (python's http.server).
# Requests under /qc/project arrive here (GET/PUT); method+path routing is done
# below with simple if...elif, following the pattern used in this codebase.
def handle_project_crud(net_request_handler, config: dict, added_data=None):

    WebResponse = config.get('iface').get('WebResponse')
    db_file = config.get('iface').get('db_file')  # a DBFile instance with CRUD methods

    def json_response(status_code, data, headers=None):
        return WebResponse(
            status_code=status_code,
            content_type='application/json',
            body=json.dumps(data, cls=JSONEncoder),
            headers=headers or [],
        )

    def read_json_body():
        body = net_request_handler.request_body.read()
        if not body:
            return None
        try:
            payload = json.loads(body)
        except ValueError:
            return None
        if not isinstance(payload, dict):
            return None
        return payload

    # ---- handlers -----------------------------------------------------------

    def handle_get_project():
        return json_response(200, {
            'project': db_file.get_project().to_dict(),
            'path': db_file.resource_path,
        })

    def handle_update_project():
        payload = read_json_body()
        if payload is None:
            return json_response(400, {'error': 'request body must be a valid JSON object'})
        try:
            project = db_file.update_project(**dict(payload))
        except ValueError as e:
            return json_response(400, {'error': f'{e}'})
        db_file.save()
        return json_response(200, {'project': project.to_dict()})

    # ---- routing ------------------------------------------------------------

    method = net_request_handler.command
    path_parsed = f'{urlparse(net_request_handler.path).path}'

    renderer = None

    if path_parsed == '/qc/project':
        if method == 'GET':
            renderer = handle_get_project
        elif method == 'PUT':
            renderer = handle_update_project

    if renderer is None:
        return json_response(405, {'error': f'renderer for {method} {path_parsed} is not recognized'})
    return renderer()

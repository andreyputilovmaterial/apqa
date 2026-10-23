from functools import partial
from urllib.parse import urlparse, unquote
import json

from .common_functions import JSONEncoder


# net_request_handler is derived from BaseHTTPRequestHandler (python's http.server).
# All requests under /qc/rules... arrive here (any HTTP method); method+path routing
# is done below with simple if...elif, following the pattern used in this codebase.
def handle_rule_crud(net_request_handler, config: dict, added_data=None):

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

    def handle_list_rules():
        rules = db_file.list_rules()
        return json_response(200, {'rules': [rule.to_dict() for rule in rules]})

    def handle_create_rule():
        payload = read_json_body()
        if payload is None:
            return json_response(400, {'error': 'request body must be a valid JSON object'})
        name = payload.get('name')
        if name is None or name == '':
            return json_response(400, {'error': "rule must have a 'name' field"})
        if db_file.has_rule(name):
            return json_response(409, {'error': f'rule already exists: {name}'})
        try:
            rule = db_file.add_rule(payload)
        except ValueError as e:
            return json_response(400, {'error': f'{e}'})
        db_file.save()
        return json_response(201, {'rule': rule.to_dict()})

    def handle_get_rule(name):
        if not db_file.has_rule(name):
            return json_response(404, {'error': f'rule not found: {name}'})
        return json_response(200, {'rule': db_file.get_rule(name).to_dict()})

    def handle_update_rule(name):
        if not db_file.has_rule(name):
            return json_response(404, {'error': f'rule not found: {name}'})
        payload = read_json_body()
        if payload is None:
            return json_response(400, {'error': 'request body must be a valid JSON object'})
        changes = dict(payload)
        if 'name' in changes:
            if changes['name'] != name:
                return json_response(400, {'error': f"use POST /qc/rules/{name}/rename to change a rule's name"})
            changes.pop('name')
        try:
            rule = db_file.update_rule(name, **changes)
        except ValueError as e:
            return json_response(400, {'error': f'{e}'})
        db_file.save()
        return json_response(200, {'rule': rule.to_dict()})

    def handle_delete_rule(name):
        if not db_file.has_rule(name):
            return json_response(404, {'error': f'rule not found: {name}'})
        deleted = db_file.delete_rule(name)
        db_file.save()
        return json_response(200, {'rule': deleted.to_dict()})

    def handle_rename_rule(name):
        if not db_file.has_rule(name):
            return json_response(404, {'error': f'rule not found: {name}'})
        payload = read_json_body()
        if payload is None:
            return json_response(400, {'error': 'request body must be a valid JSON object'})
        new_name = payload.get('new_name')
        if new_name is None or new_name == '':
            return json_response(400, {'error': "rename requires a 'new_name' field"})
        if db_file.has_rule(new_name):
            return json_response(409, {'error': f'rule already exists: {new_name}'})
        try:
            rule = db_file.rename_rule(name, new_name)
        except ValueError as e:
            return json_response(400, {'error': f'{e}'})
        db_file.save()
        return json_response(200, {'rule': rule.to_dict()})

    # ---- routing ------------------------------------------------------------

    method = net_request_handler.command
    path_with_query = net_request_handler.path
    path_parsed = f'{urlparse(path_with_query).path}'
    path_parts = [unquote(p) for p in path_parsed.split('/')]

    renderer = None

    if path_parsed == '/qc/rules':
        if method == 'GET':
            renderer = handle_list_rules
        elif method == 'POST':
            renderer = handle_create_rule
    elif len(path_parts) == 4 and path_parts[1] == 'qc' and path_parts[2] == 'rules':
        name = path_parts[3]
        if method == 'GET':
            renderer = partial(handle_get_rule, name)
        elif method == 'PUT':
            renderer = partial(handle_update_rule, name)
        elif method == 'DELETE':
            renderer = partial(handle_delete_rule, name)
    elif len(path_parts) == 5 and path_parts[1] == 'qc' and path_parts[2] == 'rules' and path_parts[4] == 'rename':
        if method == 'POST':
            renderer = partial(handle_rename_rule, path_parts[3])

    if renderer is None:
        return json_response(405, {'error': f'renderer for {method} {path_parsed} is not recognized'})
    return renderer()

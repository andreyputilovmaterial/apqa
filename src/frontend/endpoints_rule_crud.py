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

    def resolve_group(group):
        """Normalize and validate an incoming ``group`` reference to a group id."""
        if group is None:
            return ''
        try:
            return db_file.resolve_group_ref(group)
        except ValueError as e:
            raise ValueError(f'{e}')

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
        try:
            payload['group'] = resolve_group(payload.get('group'))
        except ValueError as e:
            return json_response(400, {'error': f'{e}'})
        try:
            rule = db_file.add_rule(payload)
        except ValueError as e:
            return json_response(400, {'error': f'{e}'})
        db_file.save()
        return json_response(201, {'rule': rule.to_dict()})

    def handle_get_rule(rule_id):
        if not db_file.has_rule(rule_id):
            return json_response(404, {'error': f'rule not found: {rule_id}'})
        return json_response(200, {'rule': db_file.get_rule(rule_id).to_dict()})

    def handle_update_rule(rule_id):
        if not db_file.has_rule(rule_id):
            return json_response(404, {'error': f'rule not found: {rule_id}'})
        payload = read_json_body()
        if payload is None:
            return json_response(400, {'error': 'request body must be a valid JSON object'})
        changes = dict(payload)
        if 'id' in changes:
            return json_response(400, {'error': "a rule's id cannot be changed"})
        if 'group' in changes:
            try:
                changes['group'] = resolve_group(changes['group'])
            except ValueError as e:
                return json_response(400, {'error': f'{e}'})
        try:
            rule = db_file.update_rule(rule_id, **changes)
        except ValueError as e:
            return json_response(400, {'error': f'{e}'})
        db_file.save()
        return json_response(200, {'rule': rule.to_dict()})

    def handle_delete_rule(rule_id):
        if not db_file.has_rule(rule_id):
            return json_response(404, {'error': f'rule not found: {rule_id}'})
        deleted = db_file.delete_rule(rule_id)
        db_file.save()
        return json_response(200, {'rule': deleted.to_dict()})

    def handle_rename_rule(rule_id):
        if not db_file.has_rule(rule_id):
            return json_response(404, {'error': f'rule not found: {rule_id}'})
        payload = read_json_body()
        if payload is None:
            return json_response(400, {'error': 'request body must be a valid JSON object'})
        new_name = payload.get('new_name')
        if new_name is None or new_name == '':
            return json_response(400, {'error': "rename requires a 'new_name' field"})
        try:
            rule = db_file.rename_rule(rule_id, new_name)
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
        rule_id = path_parts[3]
        if method == 'GET':
            renderer = partial(handle_get_rule, rule_id)
        elif method == 'PUT':
            renderer = partial(handle_update_rule, rule_id)
        elif method == 'DELETE':
            renderer = partial(handle_delete_rule, rule_id)
    elif len(path_parts) == 5 and path_parts[1] == 'qc' and path_parts[2] == 'rules' and path_parts[4] == 'rename':
        if method == 'POST':
            renderer = partial(handle_rename_rule, path_parts[3])

    if renderer is None:
        return json_response(405, {'error': f'renderer for {method} {path_parsed} is not recognized'})
    return renderer()

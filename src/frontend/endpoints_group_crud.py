from functools import partial
from urllib.parse import urlparse, unquote
import json

from .common_functions import JSONEncoder


# net_request_handler is derived from BaseHTTPRequestHandler (python's http.server).
# All requests under /qc/groups... arrive here (any HTTP method); method+path
# routing is done below with simple if...elif, following the pattern used in this codebase.
def handle_group_crud(net_request_handler, config: dict, added_data=None):

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

    def handle_list_groups():
        groups = db_file.list_groups()
        return json_response(200, {'groups': [g.to_dict() for g in groups]})

    def handle_create_group():
        payload = read_json_body()
        if payload is None:
            return json_response(400, {'error': 'request body must be a valid JSON object'})
        name = payload.get('name')
        if name is None or name == '':
            return json_response(400, {'error': "group must have a 'name' field"})
        try:
            group = db_file.add_group(payload)
        except ValueError as e:
            return json_response(400, {'error': f'{e}'})
        db_file.save()
        return json_response(201, {'group': group.to_dict()})

    def handle_get_group(group_id):
        if not db_file.has_group(group_id):
            return json_response(404, {'error': f'group not found: {group_id}'})
        return json_response(200, {'group': db_file.get_group(group_id).to_dict()})

    def handle_update_group(group_id):
        if not db_file.has_group(group_id):
            return json_response(404, {'error': f'group not found: {group_id}'})
        payload = read_json_body()
        if payload is None:
            return json_response(400, {'error': 'request body must be a valid JSON object'})
        changes = dict(payload)
        if 'id' in changes:
            return json_response(400, {'error': "a group's id cannot be changed"})
        try:
            group = db_file.update_group(group_id, **changes)
        except ValueError as e:
            return json_response(400, {'error': f'{e}'})
        db_file.save()
        return json_response(200, {'group': group.to_dict()})

    def handle_delete_group(group_id):
        if not db_file.has_group(group_id):
            return json_response(404, {'error': f'group not found: {group_id}'})
        try:
            deleted = db_file.delete_group(group_id)
        except ValueError as e:
            return json_response(409, {'error': f'{e}'})
        db_file.save()
        return json_response(200, {'group': deleted.to_dict()})

    def handle_rename_group(group_id):
        if not db_file.has_group(group_id):
            return json_response(404, {'error': f'group not found: {group_id}'})
        payload = read_json_body()
        if payload is None:
            return json_response(400, {'error': 'request body must be a valid JSON object'})
        new_name = payload.get('new_name')
        if new_name is None or new_name == '':
            return json_response(400, {'error': "rename requires a 'new_name' field"})
        try:
            group = db_file.rename_group(group_id, new_name)
        except ValueError as e:
            return json_response(400, {'error': f'{e}'})
        db_file.save()
        return json_response(200, {'group': group.to_dict()})

    # ---- routing ------------------------------------------------------------

    method = net_request_handler.command
    path_with_query = net_request_handler.path
    path_parsed = f'{urlparse(path_with_query).path}'
    path_parts = [unquote(p) for p in path_parsed.split('/')]

    renderer = None

    if path_parsed == '/qc/groups':
        if method == 'GET':
            renderer = handle_list_groups
        elif method == 'POST':
            renderer = handle_create_group
    elif len(path_parts) == 4 and path_parts[1] == 'qc' and path_parts[2] == 'groups':
        group_id = path_parts[3]
        if method == 'GET':
            renderer = partial(handle_get_group, group_id)
        elif method == 'PUT':
            renderer = partial(handle_update_group, group_id)
        elif method == 'DELETE':
            renderer = partial(handle_delete_group, group_id)
    elif len(path_parts) == 5 and path_parts[1] == 'qc' and path_parts[2] == 'groups' and path_parts[4] == 'rename':
        if method == 'POST':
            renderer = partial(handle_rename_group, path_parts[3])

    if renderer is None:
        return json_response(405, {'error': f'renderer for {method} {path_parsed} is not recognized'})
    return renderer()

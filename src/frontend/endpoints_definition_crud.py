from functools import partial
from urllib.parse import urlparse, unquote
import json

from .common_functions import JSONEncoder


# net_request_handler is derived from BaseHTTPRequestHandler (python's http.server).
# All requests under /qc/definitions... arrive here (any HTTP method); method+path
# routing is done below with simple if...elif, following the pattern used in this codebase.
def handle_definition_crud(net_request_handler, config: dict, added_data=None):

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

    def handle_list_definitions():
        definitions = db_file.list_definitions()
        return json_response(200, {'definitions': [d.to_dict() for d in definitions]})

    def handle_create_definition():
        payload = read_json_body()
        if payload is None:
            return json_response(400, {'error': 'request body must be a valid JSON object'})
        name = payload.get('name')
        if name is None or name == '':
            return json_response(400, {'error': "definition must have a 'name' field"})
        if db_file.has_definition(name):
            return json_response(409, {'error': f'definition already exists: {name}'})
        try:
            definition = db_file.add_definition(payload)
        except ValueError as e:
            return json_response(400, {'error': f'{e}'})
        db_file.save()
        return json_response(201, {'definition': definition.to_dict()})

    def handle_get_definition(name):
        if not db_file.has_definition(name):
            return json_response(404, {'error': f'definition not found: {name}'})
        return json_response(200, {'definition': db_file.get_definition(name).to_dict()})

    def handle_update_definition(name):
        if not db_file.has_definition(name):
            return json_response(404, {'error': f'definition not found: {name}'})
        payload = read_json_body()
        if payload is None:
            return json_response(400, {'error': 'request body must be a valid JSON object'})
        changes = dict(payload)
        if 'name' in changes:
            if changes['name'] != name:
                return json_response(400, {'error': f"use POST /qc/definitions/{name}/rename to change a definition's name"})
            changes.pop('name')
        try:
            definition = db_file.update_definition(name, **changes)
        except ValueError as e:
            return json_response(400, {'error': f'{e}'})
        db_file.save()
        return json_response(200, {'definition': definition.to_dict()})

    def handle_delete_definition(name):
        if not db_file.has_definition(name):
            return json_response(404, {'error': f'definition not found: {name}'})
        deleted = db_file.delete_definition(name)
        db_file.save()
        return json_response(200, {'definition': deleted.to_dict()})

    def handle_rename_definition(name):
        if not db_file.has_definition(name):
            return json_response(404, {'error': f'definition not found: {name}'})
        payload = read_json_body()
        if payload is None:
            return json_response(400, {'error': 'request body must be a valid JSON object'})
        new_name = payload.get('new_name')
        if new_name is None or new_name == '':
            return json_response(400, {'error': "rename requires a 'new_name' field"})
        if db_file.has_definition(new_name):
            return json_response(409, {'error': f'definition already exists: {new_name}'})
        try:
            definition = db_file.rename_definition(name, new_name)
        except ValueError as e:
            return json_response(400, {'error': f'{e}'})
        db_file.save()
        return json_response(200, {'definition': definition.to_dict()})

    # ---- routing ------------------------------------------------------------

    method = net_request_handler.command
    path_with_query = net_request_handler.path
    path_parsed = f'{urlparse(path_with_query).path}'
    path_parts = [unquote(p) for p in path_parsed.split('/')]

    renderer = None

    if path_parsed == '/qc/definitions':
        if method == 'GET':
            renderer = handle_list_definitions
        elif method == 'POST':
            renderer = handle_create_definition
    elif len(path_parts) == 4 and path_parts[1] == 'qc' and path_parts[2] == 'definitions':
        name = path_parts[3]
        if method == 'GET':
            renderer = partial(handle_get_definition, name)
        elif method == 'PUT':
            renderer = partial(handle_update_definition, name)
        elif method == 'DELETE':
            renderer = partial(handle_delete_definition, name)
    elif len(path_parts) == 5 and path_parts[1] == 'qc' and path_parts[2] == 'definitions' and path_parts[4] == 'rename':
        if method == 'POST':
            renderer = partial(handle_rename_definition, path_parts[3])

    if renderer is None:
        return json_response(405, {'error': f'renderer for {method} {path_parsed} is not recognized'})
    return renderer()

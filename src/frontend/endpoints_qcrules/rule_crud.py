from functools import partial
from urllib.parse import urlparse, unquote
import json

from ..common_functions import JSONEncoder, path_relative_to


# net_request_handler is derived from BaseHTTPRequestHandler (python's http.server).
def handle_rule_crud(net_request_handler, config: dict, added_data=None):
    """QC-rule CRUD, dispatched from the ``/qc/rules`` route.

    Requests (``<mount>`` = the route registered in ``src/endpoints.py`` and
    passed via ``added_data``; ids come from the URL path, the rest from a JSON
    request body, nothing from query/GET params):

    - ``GET <mount>`` -> `handle_list_rules`: list all rules.
    - ``POST <mount>`` (JSON body: new rule) -> `handle_create_rule`: add a rule.
    - ``GET <mount>/<id>`` -> `handle_get_rule`: fetch one rule.
    - ``PUT <mount>/<id>`` (JSON body: fields to change) -> `handle_update_rule`: patch a rule.
    - ``DELETE <mount>/<id>`` -> `handle_delete_rule`: delete a rule.
    - ``POST <mount>/<id>/rename`` (JSON body: ``{"new_name": ...}``) -> `handle_rename_rule`: rename a rule.
    - ``POST <mount>/<id>/duplicate`` -> `handle_duplicate_rule`: copy a rule.

    Persistence is delegated to ``config['iface']['db_file']`` (see ``src/db_processors``).
    """

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

    def handle_duplicate_rule(rule_id):
        if not db_file.has_rule(rule_id):
            return json_response(404, {'error': f'rule not found: {rule_id}'})
        try:
            rule = db_file.duplicate_rule(rule_id)
        except (ValueError, KeyError) as e:
            return json_response(400, {'error': f'{e}'})
        db_file.save()
        return json_response(201, {'rule': rule.to_dict()})

    # ---- routing ------------------------------------------------------------

    method = net_request_handler.command
    path_with_query = net_request_handler.path
    path_parsed = f'{urlparse(path_with_query).path}'
    # `added_data` is the mount point this handler was registered at (see
    # src/endpoints.py). Route on the path *below* it: '' for the collection,
    # '/<id>' for an item, '/<id>/rename' or '/<id>/duplicate' for an action.
    relative = path_relative_to(path_parsed, added_data)
    segments = relative.split('/') if relative is not None else None

    renderer = None

    if segments is not None:
        if len(segments) == 1 and segments[0] == '':
            if method == 'GET':
                renderer = handle_list_rules
            elif method == 'POST':
                renderer = handle_create_rule
        elif len(segments) == 2 and segments[0] == '':
            rule_id = unquote(segments[1])
            if method == 'GET':
                renderer = partial(handle_get_rule, rule_id)
            elif method == 'PUT':
                renderer = partial(handle_update_rule, rule_id)
            elif method == 'DELETE':
                renderer = partial(handle_delete_rule, rule_id)
        elif len(segments) == 3 and segments[0] == '':
            rule_id = unquote(segments[1])
            if segments[2] == 'rename' and method == 'POST':
                renderer = partial(handle_rename_rule, rule_id)
            elif segments[2] == 'duplicate' and method == 'POST':
                renderer = partial(handle_duplicate_rule, rule_id)

    if renderer is None:
        return json_response(405, {'error': f'renderer for {method} {path_parsed} is not recognized'})
    return renderer()


from urllib.parse import urlparse
import json

from ..common_functions import JSONEncoder, path_relative_to


# net_request_handler is derived from BaseHTTPRequestHandler (python's http.server).
def handle_reorder(net_request_handler, config: dict, added_data=None):
    """Move a rule or group to a new tree position, dispatched from ``/qc/reorder``.

    Requests (``<mount>`` = the route registered in ``src/endpoints.py`` and
    passed via ``added_data``; everything arrives as a JSON request body):

    - ``POST <mount>`` (JSON body: ``{"kind": "rule"|"group", "id", "parent", "before"}``)
      -> `db_file.reorder`: move the item and renumber its siblings.

    Reordering is delegated to ``config['iface']['db_file'].reorder`` (see ``src/db_processors``).
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

    method = net_request_handler.command
    path_parsed = f'{urlparse(net_request_handler.path).path}'
    if path_relative_to(path_parsed, added_data) != '' or method != 'POST':
        return json_response(405, {'error': f'renderer for {method} {path_parsed} is not recognized'})

    body = net_request_handler.request_body.read()
    try:
        payload = json.loads(body) if body else None
    except ValueError:
        payload = None
    if not isinstance(payload, dict):
        return json_response(400, {'error': 'request body must be a valid JSON object'})

    kind = payload.get('kind')
    item_id = payload.get('id')
    parent = payload.get('parent')
    before = payload.get('before')

    if kind not in ('rule', 'group'):
        return json_response(400, {'error': "a 'kind' of 'rule' or 'group' is required"})
    if item_id is None or f'{item_id}' == '':
        return json_response(400, {'error': "an 'id' field is required"})

    try:
        moved = db_file.reorder(kind, item_id, parent=parent, before=before)
    except KeyError as e:
        return json_response(404, {'error': f'{e}'})
    except ValueError as e:
        return json_response(400, {'error': f'{e}'})

    db_file.save()
    return json_response(200, {kind: moved.to_dict()})

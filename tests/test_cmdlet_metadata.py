"""Tests for the cmdlet/op editor-metadata endpoint."""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from src.cmdlets.meta import get_cmdlet_metadata
from src.frontend.endpoints_functionality import handle_functionality
from src.webserver_engine.webserve.src.common_defs import WebResponse


class FakeRequest:
    def __init__(self, method, path, body=b''):
        self.command = method
        self.path = path
        self._body = body
        self.request_body = self

    def read(self):
        return self._body


@pytest.fixture
def config():
    return {
        'iface': {
            'WebResponse': WebResponse,
            'get_cmdlet_metadata': get_cmdlet_metadata,
        },
    }


def test_metadata_shape():
    metadata = get_cmdlet_metadata()
    assert set(metadata) == {'cmdlets', 'ops'}
    assert isinstance(metadata['cmdlets'], list)
    assert isinstance(metadata['ops'], list)


def test_every_cmdlet_has_editor_fields():
    for cmdlet in get_cmdlet_metadata()['cmdlets']:
        assert cmdlet['name']
        assert cmdlet['kind'] in ('source', 'processor', 'terminal')
        assert isinstance(cmdlet['args'], list)
        assert isinstance(cmdlet['help'], str)


def test_source_readers_are_marked_as_sources():
    kinds = {c['name']: c['kind'] for c in get_cmdlet_metadata()['cmdlets']}
    assert kinds['get-content-excel'] == 'source'
    assert kinds['get-content-mdd'] == 'source'
    assert kinds['get-content-text'] == 'source'
    assert kinds['get-content'] == 'source'
    assert kinds['literal'] == 'source'
    # Processors cannot be the first cmdlet in a chain.
    assert kinds['as-date'] == 'processor'
    assert kinds['count'] == 'processor'
    assert kinds['is-sysmissing'] == 'terminal'


def test_network_cmdlet_kinds():
    kinds = {c['name']: c['kind'] for c in get_cmdlet_metadata()['cmdlets']}
    # Fetching takes the URL from the piped value, so it is a processor, not a
    # source reader; the validator is a terminal predicate.
    assert kinds['get-content-network-fetch'] == 'processor'
    assert kinds['validate-network-request-result'] == 'terminal'


def test_every_cmdlet_has_permission_list():
    for cmdlet in get_cmdlet_metadata()['cmdlets']:
        assert isinstance(cmdlet['permissions'], list)


def test_cmdlet_permission_groups():
    perms = {c['name']: c['permissions'] for c in get_cmdlet_metadata()['cmdlets']}
    filesystem_readers = (
        'get-content',
        'get-content-text',
        'get-content-excel',
        'get-content-mdd',
    )
    for name in filesystem_readers:
        assert perms[name] == ['filesystem']
    assert perms['get-content-network-fetch'] == ['network']
    # `validate-network-request-result` only inspects an already-fetched block;
    # it makes no request itself, so it requires no group.
    assert perms['validate-network-request-result'] == []
    for name, groups in perms.items():
        if name not in filesystem_readers and name != 'get-content-network-fetch':
            assert groups == []


def test_shape_cmdlet_kinds_and_args():
    meta = {c['name']: c for c in get_cmdlet_metadata()['cmdlets']}
    for name in ('select-field', 'select-item', 'select-range', 'map', 'where'):
        assert meta[name]['kind'] == 'processor'

    select_field_args = {a['name']: a for a in meta['select-field']['args']}
    assert select_field_args['field']['type'] == 'text'
    assert select_field_args['field']['required'] is True

    select_item_args = {a['name']: a for a in meta['select-item']['args']}
    assert select_item_args['index']['type'] == 'number'

    select_range_args = {a['name']: a for a in meta['select-range']['args']}
    assert select_range_args['start']['type'] == 'number'
    assert select_range_args['stop']['type'] == 'number'

    map_args = {a['name']: a for a in meta['map']['args']}
    assert map_args['transform']['type'] == 'cmdlet-chain'

    where_args = {a['name']: a for a in meta['where']['args']}
    assert where_args['predicate']['type'] == 'cmdlet-chain'


def test_comparison_ops_and_op_args():
    ops = {o['name']: o for o in get_cmdlet_metadata()['ops']}
    for name in ('cmp-eq', 'cmp-ne', 'cmp-eq-unordered', 'cmp-lt', 'cmp-le', 'cmp-gt', 'cmp-ge', 'cmp-contains'):
        assert name in ops
    eq_args = {a['name']: a for a in ops['cmp-eq']['op_args']}
    assert eq_args['unordered_arrays']['type'] == 'boolean'


def test_cmdlet_display_specs():
    meta = {c['name']: c for c in get_cmdlet_metadata()['cmdlets']}
    # get-content-excel declares a role-bearing compact spec; no `full` override
    # (the full form is the default "name args" rendering).
    assert meta['get-content-excel']['compact'] == [
        {'text': '[xlsx]', 'role': 'logo'},
        {'arg': 'path'},
    ]
    assert 'full' not in meta['get-content-excel']
    # literal renders as its value only, in both forms.
    assert meta['literal']['compact'] == [{'arg': 'value'}]
    assert meta['literal']['full'] == [{'arg': 'value'}]
    # select-field reads as an arrow in the compact view (no `full` override).
    assert meta['select-field']['compact'] == [
        {'text': '->', 'role': 'arrow'},
        {'arg': 'field'},
    ]
    assert 'full' not in meta['select-field']
    # A cmdlet without a spec carries no compact/full keys (default rendering).
    assert 'compact' not in meta['count']
    assert 'full' not in meta['count']


def test_filter_ignorelist_arg_is_strings_list():
    meta = {c['name']: c for c in get_cmdlet_metadata()['cmdlets']}
    ignorelist = {a['name']: a for a in meta['filter']['args']}['ignorelist']
    assert ignorelist['type'] == 'strings'
    assert ignorelist['required'] is True
    assert 'first_kinds' not in ignorelist


def test_literal_value_arg_is_typed():
    meta = {c['name']: c for c in get_cmdlet_metadata()['cmdlets']}
    value_args = {a['name']: a for a in meta['literal']['args']}
    assert value_args['value']['type'] == 'literal-value'
    assert value_args['value']['required'] is True


def test_comparison_op_compact_symbols():
    ops = {o['name']: o for o in get_cmdlet_metadata()['ops']}
    for name, symbol in (('cmp-eq', '='), ('cmp-ne', '≠'), ('cmp-lt', '<'), ('cmp-le', '≤'), ('cmp-gt', '>'), ('cmp-ge', '≥')):
        assert ops[name]['compact'] == [{'text': symbol, 'role': 'symbol'}]
    # Ops without a short symbol fall back to their name (no compact spec).
    assert 'compact' not in ops['cmp-contains']
    assert 'compact' not in ops['cmp-eq-unordered']


def test_normalize_display():
    from src.cmdlets.registry import normalize_display

    assert normalize_display(None) is None
    assert normalize_display('literal') == [{'text': 'literal'}]
    assert normalize_display([
        {'text': '[xlsx]', 'role': 'logo'},
        {'arg': 'path'},
    ]) == [
        {'text': '[xlsx]', 'role': 'logo'},
        {'arg': 'path'},
    ]

    with pytest.raises(ValueError):
        normalize_display([{'name': 'neither text nor arg'}])
    with pytest.raises(ValueError):
        normalize_display([{'text': 'x', 'arg': 'y'}])
    with pytest.raises(ValueError):
        normalize_display(42)


def test_normalize_permissions():
    from src.cmdlets.registry import normalize_permissions

    assert normalize_permissions(None) == []
    assert normalize_permissions('network') == ['network']
    assert normalize_permissions(['network', 'filesystem', 'network']) == [
        'filesystem',
        'network',
    ]
    with pytest.raises(ValueError):
        normalize_permissions(42)
    with pytest.raises(ValueError):
        normalize_permissions(['ok', ''])


def test_endpoint_returns_metadata(config):
    resp = handle_functionality(FakeRequest('GET', '/functionality/cmdlet-metadata'), config)
    assert resp.status_code == 200
    data = json.loads(resp.body)
    assert set(data) == {'cmdlets', 'ops'}
    assert any(c['name'] == 'get-content-excel' for c in data['cmdlets'])


def test_endpoint_metadata_unavailable():
    config = {'iface': {'WebResponse': WebResponse}}
    resp = handle_functionality(FakeRequest('GET', '/functionality/cmdlet-metadata'), config)
    assert resp.status_code == 404

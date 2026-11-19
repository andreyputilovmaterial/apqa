"""Tests for the cmdlet/op editor-metadata endpoint."""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from src.cmdlets.meta import get_cmdlet_metadata
from src.frontend.endpoints_cmdlets import handle_cmdlets
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
    assert kinds['get-filesystem-obj-info'] == 'source'
    assert kinds['literal'] == 'source'
    assert kinds['literal-from-json'] == 'source'
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


def test_validate_text_matches_is_terminal():
    kinds = {c['name']: c['kind'] for c in get_cmdlet_metadata()['cmdlets']}
    assert kinds['validate-text-matches'] == 'terminal'
    assert 'matches' not in kinds


def test_every_cmdlet_has_permission_list():
    for cmdlet in get_cmdlet_metadata()['cmdlets']:
        assert isinstance(cmdlet['permissions'], list)


def test_cmdlet_permission_groups():
    perms = {c['name']: c['permissions'] for c in get_cmdlet_metadata()['cmdlets']}
    # Stdlib file readers keep their `filesystem` capability group and default to
    # the `deps-stdlib-only` dependency group.
    for name in ('get-content', 'get-content-text', 'get-filesystem-obj-info'):
        assert perms[name] == ['deps-stdlib-only', 'filesystem']
    # Extended-dependency file readers carry the `deps-extended` umbrella plus the
    # specific library group, alongside `filesystem`.
    assert perms['get-content-excel'] == [
        'deps-extended', 'deps-extended-openpyxl', 'filesystem',
    ]
    assert perms['get-content-mdd'] == [
        'deps-extended', 'deps-extended-win32com', 'filesystem',
    ]
    assert perms['get-content-network-fetch'] == ['deps-stdlib-only', 'network']
    assert perms['transform-strip-html'] == [
        'deps-extended', 'deps-extended-beautifulsoup4',
    ]
    # `validate-network-request-result` only inspects an already-fetched block; it
    # makes no request itself, so it needs no capability group — only the stdlib
    # default dependency group.
    assert perms['validate-network-request-result'] == ['deps-stdlib-only']
    special = {
        'get-content',
        'get-content-text',
        'get-filesystem-obj-info',
        'get-content-excel',
        'get-content-mdd',
        'get-content-network-fetch',
        'transform-strip-html',
    }
    for name, groups in perms.items():
        if name not in special:
            assert groups == ['deps-stdlib-only']


def test_shape_cmdlet_kinds_and_args():
    meta = {c['name']: c for c in get_cmdlet_metadata()['cmdlets']}
    for name in ('select-field', 'select-item', 'select-range', 'foreach-item', 'where'):
        assert meta[name]['kind'] == 'processor'

    select_field_args = {a['name']: a for a in meta['select-field']['args']}
    assert select_field_args['field']['type'] == 'text'
    assert select_field_args['field']['required'] is True

    select_item_args = {a['name']: a for a in meta['select-item']['args']}
    assert select_item_args['index']['type'] == 'number'

    select_range_args = {a['name']: a for a in meta['select-range']['args']}
    assert select_range_args['start']['type'] == 'number'
    assert select_range_args['stop']['type'] == 'number'

    foreach_item_args = {a['name']: a for a in meta['foreach-item']['args']}
    assert foreach_item_args['transform']['type'] == 'cmdlet-chain'

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
    assert meta['get-filesystem-obj-info']['compact'] == [
        {'text': '[file]', 'role': 'logo'},
        {'arg': 'path'},
    ]
    assert 'full' not in meta['get-filesystem-obj-info']
    # literal renders as its value only, in both forms.
    assert meta['literal']['compact'] == [{'arg': 'value'}]
    assert meta['literal']['full'] == [{'arg': 'value'}]
    # literal-from-json mirrors literal (the JSON text is its value).
    assert meta['literal-from-json']['compact'] == [{'arg': 'value'}]
    assert meta['literal-from-json']['full'] == [{'arg': 'value'}]
    # select-field reads as an arrow in the compact view (no `full` override).
    assert meta['select-field']['compact'] == [
        {'text': '->', 'role': 'arrow'},
        {'arg': 'field'},
    ]
    assert 'full' not in meta['select-field']
    # A cmdlet without a spec carries no compact/full keys (default rendering).
    assert 'compact' not in meta['count']
    assert 'full' not in meta['count']


def test_logical_bitwise_short_forms():
    meta = {c['name']: c for c in get_cmdlet_metadata()['cmdlets']}

    def assert_short_form(name, keyword):
        assert meta[name]['compact'] == [
            {'text': f'{keyword}('},
            {'arg': 'operands', 'role': 'operands'},
            {'text': ')'},
        ]
        assert 'full' not in meta[name]

    assert_short_form('logical-and', 'AND')
    assert_short_form('logical-or', 'OR')
    assert_short_form('logical-tristate-and', 'AND')
    assert_short_form('logical-tristate-or', 'OR')
    assert_short_form('bitwise-and', 'BITAND')
    assert_short_form('bitwise-or', 'BITOR')
    assert_short_form('bitwise-xor', 'BITXOR')
    assert_short_form('bitwise-lshift', 'BITLSHIFT')
    assert_short_form('bitwise-rshift', 'BITRSHIFT')


def test_exclude_cmdlets_rules_arg_is_path_rules():
    meta = {c['name']: c for c in get_cmdlet_metadata()['cmdlets']}
    for name in ('exclude-child', 'exclude-deep-node'):
        rules = {a['name']: a for a in meta[name]['args']}['rules']
        assert rules['type'] == 'path-rules'
        assert rules['required'] is True
        assert 'first_kinds' not in rules


def test_include_cmdlets_rules_arg_is_path_rules():
    meta = {c['name']: c for c in get_cmdlet_metadata()['cmdlets']}
    for name in ('include-child', 'include-deep-node'):
        rules = {a['name']: a for a in meta[name]['args']}['rules']
        assert rules['type'] == 'path-rules'
        assert rules['required'] is True
        assert 'first_kinds' not in rules


def test_literal_value_arg_is_typed():
    meta = {c['name']: c for c in get_cmdlet_metadata()['cmdlets']}
    value_args = {a['name']: a for a in meta['literal']['args']}
    assert value_args['value']['type'] == 'literal-value'
    assert value_args['value']['required'] is True


def test_literal_from_json_value_arg_is_text():
    meta = {c['name']: c for c in get_cmdlet_metadata()['cmdlets']}
    value_args = {a['name']: a for a in meta['literal-from-json']['args']}
    assert value_args['value']['type'] == 'text'
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

    assert normalize_permissions(None) == ['deps-stdlib-only']
    assert normalize_permissions('network') == ['deps-stdlib-only', 'network']
    assert normalize_permissions(['network', 'filesystem', 'network']) == [
        'deps-stdlib-only',
        'filesystem',
        'network',
    ]
    assert normalize_permissions(
        ['deps-extended', 'deps-extended-openpyxl', 'filesystem'],
    ) == ['deps-extended', 'deps-extended-openpyxl', 'filesystem']
    with pytest.raises(ValueError):
        normalize_permissions(42)
    with pytest.raises(ValueError):
        normalize_permissions(['ok', ''])
    with pytest.raises(ValueError):
        normalize_permissions(['deps-stdlib-only', 'deps-extended'])


def test_endpoint_returns_metadata(config):
    resp = handle_cmdlets(FakeRequest('GET', '/cmdlets/metadata'), config, added_data='/cmdlets')
    assert resp.status_code == 200
    data = json.loads(resp.body)
    assert set(data) == {'cmdlets', 'ops'}
    assert any(c['name'] == 'get-content-excel' for c in data['cmdlets'])


def test_endpoint_metadata_unavailable():
    config = {'iface': {'WebResponse': WebResponse}}
    resp = handle_cmdlets(FakeRequest('GET', '/cmdlets/metadata'), config, added_data='/cmdlets')
    assert resp.status_code == 404

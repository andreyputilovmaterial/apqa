"""Tests for the reorder endpoint (POST /qc/reorder)."""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from src.db_processors import DBFile
from src.frontend.endpoints_reorder import handle_reorder
from src.webserver_engine.webserve.src.common_defs import WebResponse


class FakeRequest:
    """Minimal stand-in for BaseHTTPRequestHandler."""

    def __init__(self, method, path, body=b''):
        self.command = method
        self.path = path
        self.headers = {}
        self._body = body
        self.request_body = self

    def read(self):
        return self._body


@pytest.fixture
def config(tmp_path):
    db_file = tmp_path / 'projects.yaml'
    db_file.write_text('{}', encoding='utf-8')
    return {'iface': {'WebResponse': WebResponse, 'db_file': DBFile(str(db_file))}}


def call(config, method='POST', path='/qc/reorder', body=None):
    if body is None:
        raw = b''
    elif isinstance(body, dict):
        raw = json.dumps(body).encode('utf-8')
    else:
        raw = body
    resp = handle_reorder(FakeRequest(method, path, raw), config)
    data = json.loads(resp.body) if resp.body else None
    return resp.status_code, data


def children_of(config, parent=''):
    """Ordered children (rules + folders interleaved) under a parent, by order."""
    db = config['iface']['db_file']
    entries = []
    for index, group in enumerate(db.list_groups()):
        if group.parent == parent:
            entries.append(('group', group.id, (group.meta or {}).get('order'), index))
    for index, rule in enumerate(db.list_rules()):
        if rule.group == parent:
            entries.append(('rule', rule.id, (rule.meta or {}).get('order'), index))
    entries.sort(key=lambda e: (e[2] if e[2] is not None else 0, 0 if e[0] == 'group' else 1, e[3]))
    return [(e[0], e[1]) for e in entries]


def add_rule(config, name, group=''):
    return config['iface']['db_file'].add_rule({'name': name, 'group': group})


def add_group(config, name, parent=''):
    return config['iface']['db_file'].add_group({'name': name, 'parent': parent})


def test_reorder_rule_before_another(config):
    add_rule(config, 'r1')
    add_rule(config, 'r2')
    add_rule(config, 'r3')

    status, data = call(config, body={'kind': 'rule', 'id': 'r3', 'parent': '', 'before': 'r:r1'})

    assert status == 200
    assert data['rule']['id'] == 'r3'
    assert children_of(config) == [('rule', 'r3'), ('rule', 'r1'), ('rule', 'r2')]


def test_reorder_rule_append_at_end(config):
    add_rule(config, 'r1')
    add_rule(config, 'r2')
    add_rule(config, 'r3')

    status, data = call(config, body={'kind': 'rule', 'id': 'r1', 'parent': ''})

    assert status == 200
    assert children_of(config) == [('rule', 'r2'), ('rule', 'r3'), ('rule', 'r1')]


def test_move_rule_into_group(config):
    add_group(config, 'Data')
    add_rule(config, 'r1')
    add_rule(config, 'r2')

    status, data = call(config, body={'kind': 'rule', 'id': 'r2', 'parent': 'Data'})

    assert status == 200
    assert data['rule']['group'] == 'data'
    assert children_of(config) == [('group', 'data'), ('rule', 'r1')]
    assert children_of(config, 'data') == [('rule', 'r2')]


def test_move_rule_out_of_group_to_top_level(config):
    add_group(config, 'Data')
    add_rule(config, 'r1', 'Data')
    add_rule(config, 'r2')

    status, data = call(config, body={'kind': 'rule', 'id': 'r1', 'parent': '', 'before': 'r:r2'})

    assert status == 200
    assert data['rule']['group'] == ''
    assert children_of(config) == [('group', 'data'), ('rule', 'r1'), ('rule', 'r2')]
    assert children_of(config, 'data') == []


def test_move_rule_before_a_folder_mixed_siblings(config):
    add_group(config, 'Folder')
    add_rule(config, 'r1')

    # Ties put folders before rules, so the initial order is [Folder, r1].
    status, data = call(config, body={'kind': 'rule', 'id': 'r1', 'parent': '', 'before': 'g:folder'})

    assert status == 200
    assert children_of(config) == [('rule', 'r1'), ('group', 'folder')]


def test_move_group_inside_group(config):
    add_group(config, 'Data')
    add_group(config, 'Metadata')

    status, data = call(config, body={'kind': 'group', 'id': 'metadata', 'parent': 'Data'})

    assert status == 200
    assert data['group']['parent'] == 'data'
    assert children_of(config, 'data') == [('group', 'metadata')]
    assert children_of(config) == [('group', 'data')]


def test_reject_group_into_own_descendant(config):
    add_group(config, 'Data')
    add_group(config, 'Metadata', 'Data')

    status, data = call(config, body={'kind': 'group', 'id': 'data', 'parent': 'Metadata'})

    assert status == 400


def test_reject_unknown_sibling(config):
    add_rule(config, 'r1')
    add_rule(config, 'r2')

    status, data = call(config, body={'kind': 'rule', 'id': 'r1', 'parent': '', 'before': 'r:nope'})

    assert status == 400


def test_reject_unknown_kind(config):
    status, data = call(config, body={'kind': 'folder', 'id': 'r1', 'parent': ''})
    assert status == 400


def test_reject_missing_id(config):
    status, data = call(config, body={'kind': 'rule', 'parent': ''})
    assert status == 400


def test_reject_invalid_before_prefix(config):
    add_rule(config, 'r1')
    status, data = call(config, body={'kind': 'rule', 'id': 'r1', 'parent': '', 'before': 'r1'})
    assert status == 400


def test_reject_non_post(config):
    status, data = call(config, method='GET', path='/qc/reorder')
    assert status == 405

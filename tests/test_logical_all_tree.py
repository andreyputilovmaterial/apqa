"""End-to-end tests for `logical-all` over a compound tree.

Covers the "validate the whole tree" pattern both ways: a validation cmdlet
that already walks the tree (`validate-xml-compatible`), and the equivalent
pipeline `foreach-deep-node` (apply the validator to each leaf) followed by
`logical-all`. The two must produce the same boolean result, and the diagnostic
note path for a failing leaf must be identical.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.rule_runner import run_rule, run_rule_with_report


def _literal(value):
    return {'cmdlet': 'literal', 'args': {'value': value}}


def _validate():
    return {'cmdlet': 'validate-xml-compatible'}


def _sample_object():
    return {
        'Fields': {
            'BrandAwareness': {
                'Label': 'Awareness',
                'Text': 'Do you know <b>the brand</b>?',
            },
            'PurchaseIntent': {
                'Label': 'Purchase intent',
            },
        },
        'Pages': [
            {'Name': 'Page 1', 'Labels': ['Intro', 'Q1']},
            {'Name': 'Page 2', 'Labels': ['Q2', 'Thanks']},
        ],
    }


def _sample_object_with_bad_xml():
    value = _sample_object()
    value['Fields']['BrandAwareness']['Text'] = 'Do you know <b>the brand?'
    return value


def test_validate_xml_compatible_passes_valid_tree():
    rule = {
        'left': [_literal(_sample_object()), _validate()],
        'op': 'cmp-eq',
        'right': [_literal(True)],
    }
    assert run_rule(rule) == True


def test_foreach_deep_node_then_logical_all_passes_valid_tree():
    rule = {
        'left': [
            _literal(_sample_object()),
            {
                'cmdlet': 'foreach-deep-node',
                'args': {'transform': [_validate()]},
            },
            {'cmdlet': 'logical-all'},
        ],
        'op': 'cmp-eq',
        'right': [_literal(True)],
    }
    assert run_rule(rule) == True


def test_validate_xml_compatible_reports_failed_path():
    rule = {
        'left': [_literal(_sample_object_with_bad_xml()), _validate()],
        'op': 'cmp-eq',
        'right': [_literal(True)],
    }
    result, notes = run_rule_with_report(rule)
    assert result == False
    assert len(notes) == 1
    assert notes[0]['path'] == ['Fields', 'BrandAwareness', 'Text']
    assert 'not XML-compatible' in notes[0]['message']


def test_foreach_deep_node_then_logical_all_reports_same_failed_path():
    rule = {
        'left': [
            _literal(_sample_object_with_bad_xml()),
            {
                'cmdlet': 'foreach-deep-node',
                'args': {'transform': [_validate()]},
            },
            {'cmdlet': 'logical-all'},
        ],
        'op': 'cmp-eq',
        'right': [_literal(True)],
    }
    result, notes = run_rule_with_report(rule)
    assert result == False
    assert len(notes) == 1
    assert notes[0]['path'] == ['Fields', 'BrandAwareness', 'Text']
    assert 'not XML-compatible' in notes[0]['message']

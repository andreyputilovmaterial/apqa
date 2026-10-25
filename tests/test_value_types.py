"""Tests for the cmdlet value-type taxonomy (src/cmdlets/value_types.py)."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.cmdlets import value_types as vt


def test_scalar_categories_map_to_plain_python():
    assert vt.Text is str
    assert vt.Integer is int
    assert vt.Real is float
    assert vt.Boolean is bool
    assert vt.PathValue is Path


def test_value_taxonomy_exports_expected_names():
    for name in (
        'Value', 'PipeValue', 'Scalar', 'Compound',
        'Text', 'Integer', 'Real', 'Boolean', 'PathValue', 'DateTime',
        'CategoricalSingle', 'CategoricalMulti',
        'Block', 'NamedCollection', 'Array',
    ):
        assert hasattr(vt, name)


def test_compound_types_are_classes():
    for name in ('Value', 'Scalar', 'Compound', 'Block', 'NamedCollection', 'Array'):
        assert isinstance(getattr(vt, name), type)

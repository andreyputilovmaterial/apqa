"""Tests for build_templates.py's run-script transformation and optional-dep inlining."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import build_templates


def _run_transform(source_name, tmp_path):
    out = tmp_path / source_name
    build_templates.call_transform_run_script_program(
        ['--input', str(REPO_ROOT / source_name), '--output', str(out)],
    )
    return out.read_text(encoding='utf-8')


def test_parse_requirements_strips_comments_and_blanks():
    body = (
        '# a comment\n'
        '\n'
        'openpyxl>=3\n'
        'pywin32  # windows only\n'
        'beautifulsoup4>=4\n'
    )
    assert build_templates._parse_requirements(body) == [
        'openpyxl>=3',
        'pywin32',
        'beautifulsoup4>=4',
    ]


def test_collect_optional_dependencies_only_includes_installables():
    entries = dict(build_templates.collect_optional_dependencies())
    assert entries['get_content_excel'] == ['openpyxl>=3']
    assert entries['get_content_mdd'] == ['pywin32']
    assert entries['get_content_msmarkitdown'] == ['markitdown[pdf,xlsx,docx,pptx,xls,outlook]>=0.1.8']
    assert entries['transform_strip_html'] == ['beautifulsoup4>=4']
    # stdlib-only cmdlets have a comment-only requirements.txt → nothing to install
    assert 'get_content' not in entries
    assert 'get_content_text' not in entries
    assert 'get_content_mrs_preprocessor' not in entries
    assert 'get_content_network_fetch' not in entries
    assert 'validate_xml_compatible' not in entries
    # per-processor extras are discovered next to the cmdlet extras
    assert entries['sqlalchemy'] == ['psycopg2-binary>=2.9', 'pymysql>=1.1', 'pyodbc>=5.2']


def test_transform_run_init_sh_inlines_optional_deps(tmp_path):
    out = _run_transform('run_init.sh', tmp_path)
    assert 'optional_dependencies' not in out
    assert 'find src/cmdlets' not in out  # dev scanning loop is replaced
    assert 'BEGIN OPTIONAL-DEPS' not in out
    assert 'END OPTIONAL-DEPS' not in out
    assert "pip install 'openpyxl>=3'" in out
    assert "pip install 'pywin32'" in out
    assert "pip install 'beautifulsoup4>=4'" in out
    assert "pip install 'psycopg2-binary>=2.9'" in out
    assert 'apqa_bundle.py --program done' in out


def test_transform_run_init_bat_inlines_optional_deps(tmp_path):
    out = _run_transform('run_init.bat', tmp_path)
    assert 'optional_dependencies' not in out
    assert 'for /r' not in out  # buggy dev scanning loop is replaced
    assert 'dir /s /b' not in out
    assert 'BEGIN OPTIONAL-DEPS' not in out
    assert 'END OPTIONAL-DEPS' not in out
    assert 'pip install "openpyxl>=3"' in out
    assert 'pip install "pywin32"' in out
    assert 'pip install "beautifulsoup4>=4"' in out
    assert 'pip install "psycopg2-binary>=2.9"' in out
    assert 'apqa_bundle.py --program done' in out


def test_transform_run_tests_sh_strips_build_only_block(tmp_path):
    out = _run_transform('run_tests.sh', tmp_path)
    assert 'BEGIN BUILD-ONLY' not in out
    assert './build.sh' not in out
    assert 'pytest --import-mode=importlib apqa_bundle.py' in out

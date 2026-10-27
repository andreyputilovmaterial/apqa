"""`get-content-text` — read a text file into a single text value.

Source reader: the piped value is ignored and the file is read from ``args``.

Args (stored named mapping):
    path        required; full path to the text file.
    encoding    optional text encoding used to decode the file bytes; defaults
                to ``"utf-8"``.

The result is the decoded file content as a single text value. Reading uses the
Python standard library (``pathlib.Path.read_text``), so there is no
pip-installable dependency.
"""

from pathlib import Path

from ..registry import cmdlets
from ..value_types import PipeValue, Text

_DEFAULT_ENCODING = 'utf-8'

ARGS = [
    {
        'name': 'path',
        'type': 'path',
        'required': True,
        'description': 'Full path to the text file.',
    },
    {
        'name': 'encoding',
        'type': 'text',
        'required': False,
        'default': _DEFAULT_ENCODING,
        'description': 'Text encoding used to decode the file; defaults to utf-8.',
    },
]


@cmdlets.register(
    'get-content-text',
    kind='source',
    help='Read a text file into a single text value.',
    args=ARGS,
)
def get_content_text(value: PipeValue, args: dict) -> Text:
    path = args.get('path')
    if not path:
        raise ValueError("get-content-text: missing required arg 'path'")

    encoding = args.get('encoding') or _DEFAULT_ENCODING
    resolved = Path(path).expanduser().resolve()
    try:
        return resolved.read_text(encoding=encoding)
    except UnicodeDecodeError as error:
        raise ValueError(
            f"get-content-text: cannot decode {str(resolved)!r} as {encoding}"
        ) from error

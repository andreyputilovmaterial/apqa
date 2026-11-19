"""`get-content-msmarkitdown` — convert a file to Markdown text with MarkItDown.

Source reader: the piped value is ignored and the file is read from ``args``.

Any file MarkItDown can convert (Office documents, PDF, and other formats
covered by the installed extras) is read and returned as a single text value
holding the extracted Markdown.

Optional dependency: ``markitdown`` with the document-format extras
(``markitdown[pdf,xlsx,docx,pptx,xls,outlook]``, see ``requirements.txt``). It is
lazy-imported — loaded only when the cmdlet actually runs, never at module import
— so a missing dependency never breaks loading this module or listing the cmdlet;
only *running* the cmdlet raises a readable error (chained to the original import
error).
"""

from pathlib import Path

from ..registry import cmdlets
from ..value_types import PipeValue, Text


def _load_markitdown():
    """Import ``MarkItDown`` lazily (only when the cmdlet actually runs)."""
    try:
        from markitdown import MarkItDown
    except Exception as error:  # noqa: BLE001 - any missing-dependency failure
        raise ImportError(
            "get-content-msmarkitdown: missing optional dependency 'markitdown'"
        ) from error
    return MarkItDown


@cmdlets.register(
    'get-content-msmarkitdown',
    kind='source',
    help='Convert a file (Office, PDF, …) to Markdown text using MarkItDown.',
    args=[
        {'name': 'path', 'type': 'path', 'required': True, 'description': 'Full path to the file to convert.'},
    ],
    permissions=['filesystem', 'deps-extended', 'deps-extended-markitdown'],
    compact=[
        {'text': '[msmarkitdown]', 'role': 'logo'},
        {'arg': 'path'},
    ],
)
def get_content_msmarkitdown(value: PipeValue, args: dict) -> Text:
    MarkItDown = _load_markitdown()

    path = args.get('path')
    if not path:
        raise ValueError("get-content-msmarkitdown: missing required arg 'path'")

    resolved = Path(path).expanduser().resolve()
    result = MarkItDown().convert(str(resolved))
    if result is None:
        raise ValueError(
            f"get-content-msmarkitdown: cannot convert {str(resolved)!r} "
            "with MarkItDown (no converter matched the file)"
        )
    return Text(result.text_content or '')

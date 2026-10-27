"""`format-strip-html` — remove HTML markup from text, leaving plain text.

Terminal cmdlet: it turns a text value such as ``how <i>would</i> you rate...``
into ``how would you rate...``. The conversion is intentionally permissive:
``html.parser`` (the lenient stdlib parser behind BeautifulSoup) does best-effort
parsing of misformatted/unbalanced markup instead of rejecting it.

Value handling mirrors the other text-aware cmdlets:

- ``sysmissing`` (``None``) becomes the empty string.
- text is parsed with ``BeautifulSoup(text, "html.parser").get_text()``.
- a block (``dict``) or array (``list``) returns the same shape with every
  field/item processed recursively.
- any other scalar (a number, boolean, date/time, path, …) is converted with the
  existing `as-text` cmdlet (Python's natural ``str()``).

Optional dependency: ``beautifulsoup4`` (see ``requirements.txt``). The import is
guarded so a missing dependency never breaks loading this module or listing the
cmdlet — only *running* the cmdlet raises a readable error (chained to the
original import error).
"""

from ..as_text import as_text
from ..registry import cmdlets
from ..value_types import PipeValue, Text

try:
    from bs4 import BeautifulSoup
except Exception as error:  # noqa: BLE001 - any missing-dependency failure
    BeautifulSoup = None
    _import_error = error
else:
    _import_error = None


@cmdlets.register('format-strip-html', kind='processor')
def format_strip_html(value: PipeValue, args: dict) -> PipeValue:
    if _import_error is not None:
        raise ImportError(
            "format-strip-html: missing optional dependency 'beautifulsoup4'"
        ) from _import_error

    if value is None:
        return ''
    if isinstance(value, str):
        return _strip_html(value)
    if isinstance(value, dict):
        return {
            key: format_strip_html(field, args)
            for key, field in value.items()
        }
    if isinstance(value, list):
        return [format_strip_html(item, args) for item in value]
    return as_text(value, args)


def _strip_html(value: str) -> Text:
    """Return ``value`` with HTML tags removed (best-effort, lenient)."""
    return BeautifulSoup(value, 'html.parser').get_text()

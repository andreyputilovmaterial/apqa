"""`transform-strip-html` — remove HTML markup from text, leaving plain text.

Processor cmdlet: it turns a text value such as ``how <i>would</i> you rate...``
into ``how would you rate...``. The conversion is intentionally permissive:
``html.parser`` (the lenient stdlib parser behind BeautifulSoup) does best-effort
parsing of misformatted/unbalanced markup instead of rejecting it.

Value handling mirrors the other text-aware cmdlets:

- ``sysmissing`` becomes the empty string.
- text is parsed with ``BeautifulSoup(text, "html.parser").get_text()``.
- a block or collection returns the same shape with every leaf processed
  recursively.
- any other scalar (a number, boolean, date/time, path, …) is converted to text.

Optional dependency: ``beautifulsoup4`` (see ``requirements.txt``). It is
lazy-imported — loaded only when the cmdlet actually runs, never at module import
— so a missing dependency never breaks loading this module; only *running* the
cmdlet raises a readable error.
"""

from ..registry import cmdlets
from ..value_types import PipeValue, Text, coerce


def _get_beautifulsoup():
    """Import ``BeautifulSoup`` lazily (only when the cmdlet actually runs)."""
    try:
        from bs4 import BeautifulSoup
    except Exception as error:  # noqa: BLE001 - any missing-dependency failure
        raise ImportError(
            "transform-strip-html: missing optional dependency 'beautifulsoup4'"
        ) from error
    return BeautifulSoup


@cmdlets.register(
    'transform-strip-html',
    kind='processor',
    permissions=['deps-extended', 'deps-extended-beautifulsoup4'],
)
def transform_strip_html(value: PipeValue, args: dict) -> PipeValue:
    BeautifulSoup = _get_beautifulsoup()

    def strip_leaf(leaf, path):
        if isinstance(leaf, Text):
            return Text(_strip_html(leaf.value, BeautifulSoup))
        return Text(leaf.as_text())

    return coerce(value).map_leaves(strip_leaf)


def _strip_html(value: str, BeautifulSoup) -> str:
    """Return ``value`` with HTML tags removed (best-effort, lenient)."""
    return BeautifulSoup(value, 'html.parser').get_text()


"""`validate-xml-compatible` — check whether an incoming value can be embedded in
an XML document unchanged.

Terminal cmdlet: it answers a yes/no question about the piped value. Only ``text``
values are actually validated — the text is wrapped in a dummy root element and
parsed with ``xml.etree.ElementTree``, mirroring the snippet-level validation done
in ``report_create.py``'s ``is_xml_compatible``. This catches text that contains
unescaped markup characters (e.g. a bare ``&`` or an unbalanced tag).

Every other scalar (``sysmissing``, booleans, numbers, dates, paths, …) is not XML
markup, so it simply passes. Compound values (blocks and collections) run the same
check on every field/item and combine the results with a logical ``AND`` (an empty
compound value is vacuously valid).

When a text value fails, the cmdlet records a **diagnostic note** (if a run is
collecting notes) whose path points at the offending leaf — e.g.
``['Fields', 'BrandAwareness', 'Label']``.

``xml.etree.ElementTree`` is part of the Python standard library, so it is not a
pip-installable requirement; the import is still guarded so the module always
loads and only *running* the cmdlet raises a readable error if the module is
genuinely unavailable.
"""

from ..diagnostic import current_notes
from ..registry import cmdlets
from ..value_types import Boolean, PipeValue, Text, coerce

try:
    import xml.etree.ElementTree as ET
except Exception as error:  # noqa: BLE001 - any missing-dependency failure
    ET = None
    _import_error = error
else:
    _import_error = None


@cmdlets.register('validate-xml-compatible', kind='terminal')
def validate_xml_compatible(value: PipeValue, args: dict) -> Boolean:
    if _import_error is not None:
        raise ImportError(
            "validate-xml-compatible: missing optional dependency "
            "'xml.etree.ElementTree'"
        ) from _import_error

    return Boolean(_check(coerce(value), current_notes()))


def _check(value, notes):
    """Validate every text leaf and record a note per failing one."""
    result = True
    for leaf, path in value.iter_leaves_with_paths():
        if not isinstance(leaf, Text):
            continue
        problem = _xml_problem(leaf.value)
        if problem is not None:
            if notes is not None:
                notes.note(
                    path,
                    f'not XML-compatible: {problem} (value: {_clip(leaf.value)!r})',
                )
            result = False
    return result


def _xml_problem(text):
    """Return a human-readable reason the text is not XML-compatible, or ``None``."""
    try:
        ET.fromstring(f'<root>{text}</root>')
        return None
    except ET.ParseError as error:
        return f'{error}'


def _clip(value, limit=80):
    text = f'{value}'
    if len(text) <= limit:
        return text
    return text[:limit - 3] + '...'


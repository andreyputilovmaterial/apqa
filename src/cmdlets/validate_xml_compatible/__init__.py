"""`validate-xml-compatible` — check whether an incoming value can be embedded in
an XML document unchanged.

Terminal cmdlet: it answers a yes/no question about the piped value. Only ``text``
values are actually validated — the text is wrapped in a dummy root element and
parsed with ``xml.etree.ElementTree``, mirroring the snippet-level validation done
in ``report_create.py``'s ``is_xml_compatible``. This catches text that contains
unescaped markup characters (e.g. a bare ``&`` or an unbalanced tag).

Every other scalar (``sysmissing``, booleans, numbers, dates, paths, …) is not XML
markup, so it simply passes. Compound values (blocks and arrays) run the same check
on every field/item and combine the results with a logical ``AND`` (an empty
compound value is vacuously valid).

``xml.etree.ElementTree`` is part of the Python standard library, so it is not a
pip-installable requirement; the import is still guarded (see ``requirements.txt``)
so the module always loads, the cmdlet is always registered, and only *running* the
cmdlet raises a readable error if the module is genuinely unavailable.
"""

from ..registry import cmdlets
from ..value_types import PipeValue

try:
    import xml.etree.ElementTree as ET
except Exception as error:  # noqa: BLE001 - any missing-dependency failure
    ET = None
    _import_error = error
else:
    _import_error = None


@cmdlets.register('validate-xml-compatible')
def validate_xml_compatible(value: PipeValue, args: dict) -> bool:
    if _import_error is not None:
        raise ImportError(
            "validate-xml-compatible: missing optional dependency "
            "'xml.etree.ElementTree'"
        ) from _import_error

    if isinstance(value, str):
        return _is_xml_compatible(value)
    if isinstance(value, dict):
        return all(
            validate_xml_compatible(field_value, args)
            for field_value in value.values()
        )
    if isinstance(value, list):
        return all(validate_xml_compatible(item, args) for item in value)
    return True


def _is_xml_compatible(text: str) -> bool:
    """Return ``True`` when ``text`` can be wrapped in a root element and parsed.

    A label/snippet is considered XML-compatible when it needs no escaping to be
    placed inside an XML document. Empty text is vacuously compatible.
    """
    try:
        ET.fromstring(f'<root>{text}</root>')
        return True
    except ET.ParseError:
        return False

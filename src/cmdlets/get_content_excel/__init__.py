"""`get-content-excel` — read the first sheet of an Excel workbook into an array
of blocks (one dict per data row, keyed by header cell).

Optional dependency: ``openpyxl`` (see ``requirements.txt``). The import is
guarded so a missing dependency never breaks loading this module or listing the
cmdlet — only *running* the cmdlet raises a readable error (chained to the
original import error).
"""

from ..registry import cmdlets

try:
    import openpyxl
    from openpyxl.utils import get_column_letter
except Exception as error:  # noqa: BLE001 - any missing-dependency failure
    openpyxl = None
    get_column_letter = None
    _openpyxl_import_error = error
else:
    _openpyxl_import_error = None


@cmdlets.register('get-content-excel')
def get_content_excel(value, args):
    if _openpyxl_import_error is not None:
        raise ImportError(
            "get-content-excel: missing optional dependency 'openpyxl'"
        ) from _openpyxl_import_error

    path = args.get('path')
    if not path:
        raise ValueError("get-content-excel: missing required arg 'path'")

    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    sheet_name = args.get('sheet')
    sheet = workbook[sheet_name] if sheet_name else workbook.active

    rows = sheet.iter_rows(values_only=True)
    header = next(rows, None)
    if header is None:
        return []

    names = _deduplicate_headers(header)
    return [dict(zip(names, row)) for row in rows]


def _deduplicate_headers(header):
    """Turn raw header cells into unique field names.

    Empty cells fall back to the source's native coordinate (Excel letters);
    duplicate names get a numeric suffix (``state``, ``state.1``, ``state.2``)
    per ``docs/cmdlet-data-formats.md``.
    """
    seen = {}
    names = []
    for index, cell in enumerate(header, start=1):
        base = cell if cell not in (None, '') else get_column_letter(index)
        base = f'{base}'
        if base in seen:
            seen[base] += 1
            names.append(f'{base}.{seen[base]}')
        else:
            seen[base] = 0
            names.append(base)
    return names

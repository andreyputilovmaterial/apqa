"""`get-content-excel` — read an Excel workbook into a block of sheets.

Each sheet is keyed by its name and holds that sheet's data rows as an array of
blocks (one dict per data row, keyed by header cell). Returning every sheet —
keyed by its stable sheet name — rather than a single active sheet means a QC
rule must address the sheet it wants explicitly and never depends on which sheet
Excel happened to save as "active".

Optional dependency: ``openpyxl`` (see ``requirements.txt``). It is lazy-imported
— loaded only when the cmdlet actually runs, never at module import — so a
missing dependency never breaks loading this module or listing the cmdlet; only
*running* the cmdlet raises a readable error (chained to the original import
error).
"""

from ..registry import cmdlets
from ..value_types import Block, Collection, PipeValue, from_plain


def _load_openpyxl():
    """Import ``openpyxl`` lazily (only when the cmdlet actually runs).

    Returns ``(openpyxl, get_column_letter)``.
    """
    try:
        import openpyxl
        from openpyxl.utils import get_column_letter
    except Exception as error:  # noqa: BLE001 - any missing-dependency failure
        raise ImportError(
            "get-content-excel: missing optional dependency 'openpyxl'"
        ) from error
    return openpyxl, get_column_letter


@cmdlets.register(
    'get-content-excel',
    kind='source',
    help='Read every sheet of an Excel workbook into a block keyed by sheet name.',
    args=[
        {'name': 'path', 'type': 'path', 'required': True, 'description': 'Full path to the Excel workbook.'},
    ],
    permissions=['filesystem', 'deps-extended', 'deps-extended-openpyxl'],
    compact=[
        {'text': '[xlsx]', 'role': 'logo'},
        {'arg': 'path'},
    ],
)
def get_content_excel(value: PipeValue, args: dict) -> Block:
    openpyxl, get_column_letter = _load_openpyxl()

    path = args.get('path')
    if not path:
        raise ValueError("get-content-excel: missing required arg 'path'")

    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        return from_plain(Block({
            sheet_name: _read_sheet(workbook[sheet_name], get_column_letter)
            for sheet_name in workbook.sheetnames
        }))
    finally:
        close = getattr(workbook, 'close', None)
        if callable(close):
            close()


def _read_sheet(sheet, get_column_letter) -> Collection:
    """Read one sheet into a collection of row blocks (header row = field names)."""
    rows = sheet.iter_rows(values_only=True)
    header = next(rows, None)
    if header is None:
        return Collection([])
    names = _deduplicate_headers(header, get_column_letter)
    return Collection([Block(zip(names, row)) for row in rows])


def _deduplicate_headers(header, get_column_letter) -> list:
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

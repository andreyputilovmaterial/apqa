"""`get-content-mdd` — read an MDD metadata document into a structured block.

MDD files (IBM SPSS Data Collection / Unicom Intelligence metadata) are only
readable through the COM API exposed by MDM/Professional, so running this cmdlet
requires Windows, MDM/Professional installed, and ``pywin32`` (``win32com.client``).

Optional dependency: ``pywin32`` (see ``requirements.txt``). The import is guarded
so a missing dependency never breaks loading this module or listing the cmdlet —
only *running* the cmdlet raises a readable error (chained to the original import
error).

Args (stored named mapping):
    path        required; full path to the ``.mdd`` file.
    method      ``"open"`` (default) or ``"join"`` — see ``_open_document``.
    contexts    list (or comma-separated string) of label/property contexts,
                default ``["Question", "Analysis"]``.
    step_into   bool, default ``True``. ``True`` expands a shared-list reference
                into the referenced categories/elements; ``False`` ("step over")
                keeps the reference as a single item.

The result is a block whose top-level fields are the MDD sections:

    source_file   absolute path to the read file
    languages     array of ``{name, label}`` blocks
    shared_lists  block keyed by shared-list name (each value is a shared-list block)
    fields        block keyed by field name (each value is a field block)
    pages         block keyed by page name (each value is a page block)
    routing       the routing script as a single text value

Every item block has the metadata fields ``name``, ``label``, ``attributes``,
``properties``, ``translations``, ``scripting`` plus a ``value`` field whose shape
depends on the item kind:

    scalar (ObjectTypeValue 0)   ``value`` is ``None`` (MDD metadata has no
                                 data value). A categorical (DataType 3)
                                 additionally carries a ``categories`` block.
    array/grid (ObjectTypeValue 1/2)
                                 ``value`` is an ordered array of iteration
                                 blocks, and ``fields`` holds the loop's subfields.
    block/class (ObjectTypeValue 3)
                                 ``value`` is a block of subfields.
    shared list / page           ``value`` is an array of category/entry blocks.

Items that own categories (categorical scalars, arrays, shared lists) also carry a
``categories`` block keyed by category name → detailed category block; for a
categorical scalar the keys of ``categories`` are the available response options.
Category groups (``Type`` != 0) nest their children in their own ``value`` array
and are not selectable response options.
"""

from pathlib import Path
import re

from ..registry import cmdlets
from ..value_types import Block, PipeValue

try:
    import win32com.client as _win32com_client
except Exception as error:  # noqa: BLE001 - any missing-dependency failure
    _win32com_client = None
    _import_error = error
else:
    _import_error = None


_DEFAULT_CONTEXTS = ['Question', 'Analysis']


def _safe_get(item, attr):
    """Return ``item.<attr>`` or ``None`` when the attribute is unavailable."""
    try:
        return getattr(item, attr)
    except Exception:  # noqa: BLE001 - COM raises many error types
        return None


def _str_safe(value):
    """Return ``str(value)`` or ``None`` (never the literal ``"None"``)."""
    if value is None:
        return None
    try:
        return str(value)
    except Exception:  # noqa: BLE001
        return None


def _safe_str_get(item, attr):
    """Return ``str(item.<attr>)`` or ``None`` when unavailable/empty."""
    return _str_safe(_safe_get(item, attr))


def _as_int(value):
    if value is None:
        return None
    try:
        return int(value)
    except Exception:  # noqa: BLE001
        return None


def _plain(value):
    """Coerce a COM value to a plain Python scalar (or ``None``)."""
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    try:
        return int(value)
    except Exception:  # noqa: BLE001
        pass
    try:
        return float(value)
    except Exception:  # noqa: BLE001
        pass
    return _str_safe(value)


def _as_list(value):
    """Normalize an args value into a list (accepts a list or comma string)."""
    if value is None:
        return []
    if isinstance(value, str):
        return [part.strip() for part in value.split(',') if part.strip()]
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def _is_digit_name(name):
    if name is None:
        return False
    return re.match(r'^\s*?\d+\s*?$', name, flags=re.I | re.DOTALL) is not None


def _iter_attr(item, attr):
    """Iterate ``item.<attr>``, yielding nothing when unavailable/uniterable."""
    try:
        return iter(getattr(item, attr))
    except Exception:  # noqa: BLE001
        return iter(())


def _iter(collection):
    try:
        return iter(collection)
    except Exception:  # noqa: BLE001
        return iter(())


def _index_category(cat, result):
    name = cat.get('name')
    if name:
        result.setdefault(name, cat)
    value = cat.get('value')
    if isinstance(value, list):
        for child in value:
            _index_category(child, result)


def _category_map(category_blocks):
    result = {}
    for cat in category_blocks:
        _index_category(cat, result)
    return result


def _resolved_path(path):
    return str(Path(path).expanduser().resolve())


def _open_document(path, method):
    """Create and open an ``MDM.Document`` COM object for ``path``."""
    if method not in ('open', 'join'):
        raise ValueError(
            f"get-content-mdd: unknown method {method!r} "
            "(expected 'open' or 'join')"
        )
    if not Path(path).is_file():
        raise FileNotFoundError(f'get-content-mdd: file not found: {path}')

    try:
        document = _win32com_client.Dispatch('MDM.Document')
    except Exception as error:  # noqa: BLE001
        raise RuntimeError(
            "get-content-mdd: cannot create 'MDM.Document' COM object "
            '(is MDM/Professional installed and running on Windows?)'
        ) from error

    if method == 'open':
        # "open" is straightforward but locks the file exclusively.
        document.Open(path, '', 1)  # 1 == oREAD
    else:
        # "join" merges the document into a new empty one and does not need
        # exclusive access (a more stable fallback).
        document.Join(path, '{..}', 1, 32 | 16 | 512)
    return document


def _close_document(document):
    try:
        document.Close()
    except Exception:  # noqa: BLE001
        pass


class _MDDReader:
    def __init__(self, document, path, contexts, step_into):
        self.document = document
        self.path = path
        self.contexts = contexts or _DEFAULT_CONTEXTS
        self.step_into = step_into
        self._languages = list(_iter_attr(document, 'Languages'))
        self.langcodes = []
        for lang in self._languages:
            code = _safe_str_get(lang, 'Name') or _str_safe(lang)
            if code:
                self.langcodes.append(code)
        self.primary_context = self.contexts[0] if self.contexts else 'Question'

    def read(self):
        return {
            'source_file': self.path,
            'languages': self._read_languages(),
            'shared_lists': self._read_shared_lists(),
            'fields': self._read_fields(),
            'pages': self._read_pages(),
            'routing': self._read_routing(),
        }

    # -- sections -----------------------------------------------------------

    def _read_languages(self):
        result = []
        for lang in self._languages:
            result.append({
                'name': _safe_str_get(lang, 'Name'),
                'label': _safe_str_get(lang, 'LongName'),
            })
        return result

    def _read_shared_lists(self):
        types = _safe_get(self.document, 'Types')
        if types is None:
            return {}
        names = sorted(
            name for name in (_safe_str_get(sl, 'Name') for sl in _iter(types))
            if name
        )
        result = {}
        for sl_name in names:
            sl = types[sl_name]
            categories = self._read_category_collection(sl)
            block = self._read_item_meta(sl, self._shared_list_attributes(sl))
            block['categories'] = _category_map(categories)
            block['value'] = categories
            result[sl_name] = block
        return result

    def _read_fields(self):
        result = {}
        for field in _iter_attr(self.document, 'Fields'):
            name = _safe_str_get(field, 'Name')
            if not name:
                continue
            result[name] = self._read_field(field)
        return result

    def _read_pages(self):
        result = {}
        for page in _iter_attr(self.document, 'Pages'):
            name = _safe_str_get(page, 'Name')
            if not name:
                continue
            block = self._read_item_meta(page, {'type': 'page'})
            block['value'] = self._read_page_entries(page)
            result[name] = block
        return result

    def _read_page_entries(self, page):
        result = []
        for entry in _iter(page):
            block = self._read_item_meta(entry, {'type': 'page_entry'})
            block['value'] = None
            result.append(block)
        return result

    def _read_routing(self):
        routing = _safe_get(self.document, 'Routing')
        if routing is None:
            return None
        return _safe_str_get(routing, 'Script')

    def _shared_list_attributes(self, sl):
        attrs = {'type': 'shared_list'}
        if _safe_get(sl, 'IsReference'):
            attrs['is_reference'] = True
            ref = _safe_str_get(sl, 'ReferenceName')
            if ref:
                attrs['reference_name'] = ref
        return attrs


    # -- fields -------------------------------------------------------------

    def _read_field(self, field):
        name = _safe_str_get(field, 'Name')
        object_type_value = _as_int(_safe_get(field, 'ObjectTypeValue'))
        if object_type_value is None:
            raise ValueError(
                f"get-content-mdd: field {name!r} has no ObjectTypeValue"
            )

        if object_type_value == 0:
            block = self._read_scalar_field(field)
        elif object_type_value in (1, 2):
            block = self._read_array_field(field, object_type_value)
        elif object_type_value == 3:
            block = self._read_block_field(field)
        elif object_type_value == 16:
            block = self._read_item_meta(
                field, {'object_type_value': 16, 'type': 'plain/type16'}
            )
            block['value'] = None
        else:
            raise ValueError(
                f"get-content-mdd: field {name!r} has unrecognized "
                f'ObjectTypeValue {object_type_value}'
            )

        self._add_field_flags(field, block)
        helper_fields = self._read_helper_fields(field)
        if helper_fields:
            block['helper_fields'] = helper_fields
        return block

    def _read_scalar_field(self, field):
        data_type = _as_int(_safe_get(field, 'DataType'))
        block = self._read_item_meta(
            field, self._scalar_attributes(field, data_type)
        )
        if data_type == 3:
            block['categories'] = _category_map(
                self._read_category_collection(field)
            )
        block['value'] = None
        return block

    def _read_array_field(self, field, object_type_value):
        attrs = {
            'object_type_value': object_type_value,
            'type': 'array' if object_type_value == 1 else 'grid',
        }
        is_grid = _safe_get(field, 'IsGrid')
        if is_grid is not None:
            attrs['is_grid'] = bool(is_grid)
        block = self._read_item_meta(field, attrs)
        categories = self._read_category_collection(field)
        block['categories'] = _category_map(categories)
        block['value'] = categories
        subfields = self._read_subfields(field)
        if subfields:
            block['fields'] = subfields
        return block

    def _read_block_field(self, field):
        block = self._read_item_meta(
            field, {'object_type_value': 3, 'type': 'block'}
        )
        block['value'] = self._read_subfields(field)
        return block

    def _scalar_attributes(self, field, data_type):
        attrs = {'object_type_value': 0, 'data_type': data_type, 'type': 'plain'}
        if data_type == 0:
            attrs['type'] = 'plain/info'
        elif data_type == 1:
            attrs['type'] = 'plain/long'
            attrs['minvalue'] = _plain(_safe_get(field, 'MinValue'))
            attrs['maxvalue'] = _plain(_safe_get(field, 'MaxValue'))
        elif data_type == 2:
            attrs['type'] = 'plain/text'
            attrs['minvalue'] = _plain(_safe_get(field, 'MinValue'))
            attrs['maxvalue'] = _plain(_safe_get(field, 'MaxValue'))
        elif data_type == 3:
            attrs['type'] = 'plain/categorical'
            minv = _plain(_safe_get(field, 'MinValue'))
            maxv = _plain(_safe_get(field, 'MaxValue'))
            attrs['minvalue'] = minv
            attrs['maxvalue'] = maxv
            # MaxValue == 1 → single-punch; anything else (or missing) → multi-punch.
            attrs['categorical_kind'] = 'single' if maxv == 1 else 'multi'
        elif data_type == 5:
            attrs['type'] = 'plain/date'
        elif data_type == 6:
            attrs['type'] = 'plain/double'
            attrs['minvalue'] = _plain(_safe_get(field, 'MinValue'))
            attrs['maxvalue'] = _plain(_safe_get(field, 'MaxValue'))
        elif data_type == 7:
            attrs['type'] = 'plain/boolean'
        return attrs

    def _add_field_flags(self, field, block):
        attrs = block['attributes']
        if _safe_get(field, 'IsSystem'):
            attrs['is_system'] = True
        if _safe_get(field, 'HasCaseData') is False:
            attrs['has_case_data'] = False

    def _read_subfields(self, field):
        result = {}
        for sub in _iter_attr(field, 'Fields'):
            name = _safe_str_get(sub, 'Name')
            if not name:
                continue
            result[name] = self._read_field(sub)
        return result

    def _read_helper_fields(self, field):
        result = {}
        for helper in _iter_attr(field, 'HelperFields'):
            block = self._read_field(helper)
            name = block.get('name')
            if not name:
                continue
            block['attributes']['is_helper_field'] = True
            result[name] = block
        return result


    # -- common item metadata ----------------------------------------------

    def _read_item_meta(self, item, attributes):
        return {
            'name': _safe_str_get(item, 'Name'),
            'label': _safe_str_get(item, 'Label'),
            'attributes': attributes,
            'translations': self._read_translations(item),
            'scripting': _safe_str_get(item, 'Script'),
            'properties': self._read_properties(item),
        }

    def _read_translations(self, item):
        result = {}
        for langcode in self.langcodes:
            try:
                text = item.Labels(self.primary_context, langcode)
            except Exception:  # noqa: BLE001
                text = None
            result[langcode] = _str_safe(text)
        return result

    def _read_properties(self, item):
        document = self.document
        contexts = _safe_get(document, 'Contexts')
        context_preserve = (
            _safe_get(contexts, 'Current') if contexts is not None else None
        )

        properties = {}
        try:
            for read_context in _iter(contexts):
                ctx_name = (
                    _safe_str_get(read_context, 'Name')
                    or _str_safe(read_context)
                )
                if not ctx_name:
                    continue
                if not any(ctx_name.lower() == c.lower() for c in self.contexts):
                    continue
                try:
                    contexts.Current = read_context
                except Exception:  # noqa: BLE001
                    continue

                props = _safe_get(item, 'Properties')
                count = (
                    _as_int(_safe_get(props, 'Count'))
                    if props is not None else 0
                )
                for index in range(count or 0):
                    prop_name = self._property_name(props, index)
                    if not prop_name:
                        continue
                    value = self._property_value(props, prop_name)
                    if prop_name not in properties:
                        properties[prop_name] = value
                    elif properties[prop_name] == value:
                        continue
                    else:
                        properties[f'{prop_name} ({ctx_name})'] = value
        finally:
            if context_preserve is not None and contexts is not None:
                try:
                    contexts.Current = context_preserve
                except Exception:  # noqa: BLE001
                    pass

        return {key: properties[key] for key in sorted(properties)}

    def _property_name(self, props, index):
        try:
            return _str_safe(props.Name(index))
        except Exception:  # noqa: BLE001
            return None

    def _property_value(self, props, name):
        try:
            return _str_safe(props[name])
        except Exception:  # noqa: BLE001
            return None


    # -- categories ---------------------------------------------------------

    def _read_category_collection(self, item):
        result = []
        for cat in _iter_attr(item, 'Elements'):
            if _safe_get(cat, 'IsReference'):
                ref_name = _safe_str_get(cat, 'ReferenceName')
                if ref_name:
                    self._resolve_shared_list(ref_name)
                if self.step_into and ref_name:
                    result.extend(
                        self._read_category_collection(
                            self._resolve_shared_list(ref_name)
                        )
                    )
                else:
                    result.append(self._read_category(cat))
            else:
                result.append(self._read_category(cat))
        return result

    def _read_category(self, cat):
        is_reference = bool(_safe_get(cat, 'IsReference'))
        cat_type = _as_int(_safe_get(cat, 'Type'))
        name = _safe_str_get(cat, 'Name')
        is_group = (
            False if is_reference
            else self._is_category_group(cat, cat_type, name)
        )

        attributes = {
            'category_type': cat_type,
            'is_group': is_group,
            'is_reference': is_reference,
        }
        if is_reference:
            ref_name = _safe_str_get(cat, 'ReferenceName')
            if ref_name:
                attributes['reference_name'] = ref_name

        block = self._read_item_meta(cat, attributes)
        block['value'] = (
            self._read_category_collection(cat) if is_group else None
        )
        return block

    def _is_category_group(self, cat, cat_type, name):
        if cat_type is None:
            return self._has_elements(cat)
        if cat_type == 0:
            return False
        if cat_type in (1, 13):
            return True
        if cat_type == 4097:
            return False
        if _is_digit_name(name):
            return False
        return self._has_elements(cat)

    def _has_elements(self, item):
        try:
            iter(getattr(item, 'Elements'))
            return True
        except Exception:  # noqa: BLE001
            return False

    def _resolve_shared_list(self, reference_name):
        clean = re.sub(r'[\^\\/\.]', '', reference_name, flags=re.I | re.DOTALL)
        try:
            return self.document.Types[clean]
        except Exception as error:  # noqa: BLE001
            raise ValueError(
                f'get-content-mdd: cannot resolve shared list '
                f'{reference_name!r}'
            ) from error


@cmdlets.register(
    'get-content-mdd',
    kind='source',
    help='Read an MDD metadata document into a structured block.',
    args=[
        {'name': 'path', 'type': 'path', 'required': True, 'description': 'Full path to the .mdd file.'},
        {
            'name': 'method',
            'type': 'options',
            'required': False,
            'default': 'open',
            'options': ['open', 'join'],
            'description': 'How to open the document.',
        },
        {
            'name': 'contexts',
            'type': 'list',
            'required': False,
            'default': ['Question', 'Analysis'],
            'description': 'Label/property contexts to read.',
        },
        {
            'name': 'step_into',
            'type': 'boolean',
            'required': False,
            'default': True,
            'description': 'Expand shared-list references into their elements.',
        },
    ],
)
def get_content_mdd(value: PipeValue, args: dict) -> Block:
    if _import_error is not None:
        raise ImportError(
            "get-content-mdd: missing optional dependency 'pywin32'"
        ) from _import_error

    path = args.get('path')
    if not path:
        raise ValueError("get-content-mdd: missing required arg 'path'")

    method = args.get('method') or 'open'
    contexts = _as_list(args.get('contexts', _DEFAULT_CONTEXTS))
    step_into = bool(args.get('step_into', True))

    resolved = _resolved_path(path)
    document = _open_document(resolved, method)
    try:
        return _MDDReader(document, resolved, contexts, step_into).read()
    finally:
        _close_document(document)

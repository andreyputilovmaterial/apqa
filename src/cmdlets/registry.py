
import inspect


def normalize_args(args):
    """Normalize a list of arg schemas into the shape the UI consumes.

    Each arg is ``{'name': str, 'type': str, 'required': bool, 'description':
    str}`` plus optional ``default`` and ``options`` (for ``type='options'``).
    ``type`` defaults to ``'text'``. This is intentionally permissive — it only
    makes the minimum structural guarantees the editor needs and leaves the rest
    of the data format flexible.
    """
    result = []
    for arg in args or []:
        if not isinstance(arg, dict) or not arg.get('name'):
            raise ValueError('cmdlet arg schema must be a mapping with a name')
        normalized = {
            'name': f"{arg['name']}",
            'type': arg.get('type', 'text'),
            'required': bool(arg.get('required', False)),
            'description': arg.get('description') or '',
        }
        if 'default' in arg:
            normalized['default'] = arg['default']
        if 'options' in arg:
            normalized['options'] = list(arg['options'])
        result.append(normalized)
    return result


def normalize_display(parts):
    """Normalize a display spec (an ordered list of parts) into the shape the UI
    consumes.

    A display spec describes how one cmdlet / comparison op is rendered in a
    specific view (``compact`` or ``full``). It is an ordered list of parts, each
    one of:

    - a plain string — a literal text token;
    - ``{'text': <str>, 'role': <str>}`` — a literal token with an optional role
      (a semantic label the frontend maps to a CSS class);
    - ``{'arg': <name>}`` — the value of that cmdlet arg, rendered by the arg's
      declared type; an optional ``role`` overrides the default ``'arg'`` role.

    ``None`` means "no override" (the frontend falls back to the default
    rendering). A single string is accepted as a one-literal-part shorthand. The
    check is intentionally permissive — it only makes the minimum structural
    guarantees the renderer needs and fails early with a readable message on a
    malformed part.
    """
    if parts is None:
        return None
    if isinstance(parts, str):
        parts = [parts]
    if not isinstance(parts, (list, tuple)):
        raise ValueError('display spec must be a list of parts (or a single string)')
    result = []
    for part in parts:
        if isinstance(part, str):
            result.append({'text': part})
            continue
        if not isinstance(part, dict):
            raise ValueError('display part must be a string or a mapping')
        has_text = 'text' in part
        has_arg = 'arg' in part
        if has_text == has_arg:
            raise ValueError('display part must have exactly one of "text" or "arg"')
        normalized = {'text': f'{part["text"]}'} if has_text else {'arg': f'{part["arg"]}'}
        if 'role' in part:
            normalized['role'] = f'{part["role"]}'
        result.append(normalized)
    return result


def normalize_permissions(permissions):
    """Normalize a permission-group declaration into a sorted list of names.

    A cmdlet declares the permission groups it requires to run; most cmdlets
    require none. ``None`` means no groups and a single string is accepted as a
    one-group shorthand. The result is de-duplicated and sorted so the metadata
    stays stable.

    Group names are free-form strings; the two groups defined today are
    ``'filesystem'`` (reads/touches physical files) and ``'network'`` (makes a
    network request). Enforcement happens at run time in
    ``chain_runner.run_chain`` against the session's ``UserSettings`` (see
    ``src/user_settings.py``).
    """
    if permissions is None:
        return []
    if isinstance(permissions, str):
        permissions = [permissions]
    if not isinstance(permissions, (list, tuple)):
        raise ValueError('permissions must be a list of permission-group names')
    result = []
    for name in permissions:
        if not isinstance(name, str) or not name:
            raise ValueError('each permission group must be a non-empty string')
        result.append(name)
    return sorted(set(result))


class CmdletRegistry:
    """Global registry of cmdlets, keyed by cmdlet name.

    A cmdlet is a plain function with the signature ``(value, args) -> value``:

    - ``value`` is the incoming piped value (``None`` for the first cmdlet in a
      chain, which is expected to read its input from ``args`` instead).
    - ``args`` is the stored named-args mapping for this cmdlet.

    Register a cmdlet with the ``@cmdlets.register('<name>')`` decorator. The
    decorator also records editor metadata used by the rule form:

    - ``kind`` — ``'source'`` when the cmdlet can be the first in a chain (it
      reads/produces its input without a piped value), ``'processor'`` when it
      transforms the piped value, or ``'terminal'`` for a validation/predicate
      cmdlet that answers a question about the piped value.
    - ``args`` — a list of arg schemas (see :func:`normalize_args`); the UI
      renders one input per arg.
    - ``help`` — a short description shown in the editor; defaults to the
      function's docstring.
    - ``permissions`` — an optional list of permission-group names the cmdlet
      requires (see :func:`normalize_permissions`); empty by default. Enforced
      at run time by the chain runner against the session's ``UserSettings``
      allow-list (see ``src/user_settings.py``).
    - ``compact`` / ``full`` — optional display specs (an ordered list of parts,
      see :func:`normalize_display`) describing how the cmdlet is rendered in the
      compact and full views; absent means the default ``name args`` rendering.
    """

    def __init__(self):
        self._cmdlets = {}
        self._meta = {}

    def register(self, name, kind='processor', args=None, help=None, compact=None, full=None, permissions=None):
        def decorator(fn):
            self._cmdlets[name] = fn
            meta = {
                'name': name,
                'kind': kind,
                'args': normalize_args(args),
                'help': help if help is not None else (inspect.getdoc(fn) or ''),
                'permissions': normalize_permissions(permissions),
            }
            if compact is not None:
                meta['compact'] = normalize_display(compact)
            if full is not None:
                meta['full'] = normalize_display(full)
            self._meta[name] = meta
            return fn
        return decorator

    def get(self, name):
        if name not in self._cmdlets:
            raise KeyError(f'cmdlet not found: {name}')
        return self._cmdlets[name]

    def names(self):
        return list(self._cmdlets)

    def describe(self, name):
        return self._meta.get(name)

    def metadata(self):
        return [self._meta[name] for name in self._cmdlets]


cmdlets = CmdletRegistry()


class ComparisonRegistry:
    """Global registry of comparison ops, keyed by op name.

    A comparison op is a plain function ``(left, right, args=None) -> bool``
    comparing two values. ``args`` is an optional mapping of op-specific options
    (e.g. ``cmp-eq`` accepts ``{'unordered_arrays': True}``). Register an op with
    ``@comparisons.register('<name>')``.

    The decorator also records editor metadata: ``op_args`` (a list of arg
    schemas the rule form renders as op-specific inputs), ``help`` (a short
    description, defaulting to the function docstring), and optional ``compact``
    / ``full`` display specs (see :func:`normalize_display`) describing how the
    op is rendered in the compact and full views — e.g. ``cmp-eq`` declares
    ``compact=[{'text': '=', 'role': 'symbol'}]`` so the short symbol lives here
    rather than in a frontend hardcoded map.
    """

    def __init__(self):
        self._ops = {}
        self._meta = {}

    def register(self, name, help=None, op_args=None, compact=None, full=None):
        def decorator(fn):
            self._ops[name] = fn
            meta = {
                'name': name,
                'help': help if help is not None else (inspect.getdoc(fn) or ''),
                'op_args': normalize_args(op_args),
            }
            if compact is not None:
                meta['compact'] = normalize_display(compact)
            if full is not None:
                meta['full'] = normalize_display(full)
            self._meta[name] = meta
            return fn
        return decorator

    def get(self, name):
        if name not in self._ops:
            raise KeyError(f'comparison op not found: {name}')
        return self._ops[name]

    def names(self):
        return list(self._ops)

    def describe(self, name):
        return self._meta.get(name)

    def metadata(self):
        return [self._meta[name] for name in self._ops]


comparisons = ComparisonRegistry()

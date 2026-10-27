
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
    """

    def __init__(self):
        self._cmdlets = {}
        self._meta = {}

    def register(self, name, kind='processor', args=None, help=None):
        def decorator(fn):
            self._cmdlets[name] = fn
            self._meta[name] = {
                'name': name,
                'kind': kind,
                'args': normalize_args(args),
                'help': help if help is not None else (inspect.getdoc(fn) or ''),
            }
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

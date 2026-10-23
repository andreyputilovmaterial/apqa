
class CmdletRegistry:
    """Global registry of cmdlets, keyed by cmdlet name.

    A cmdlet is a plain function with the signature ``(value, args) -> value``:

    - ``value`` is the incoming piped value (``None`` for the first cmdlet in a
      chain, which is expected to read its input from ``args`` instead).
    - ``args`` is the stored named-args mapping for this cmdlet.

    Register a cmdlet with the ``@cmdlets.register('<name>')`` decorator.
    """

    def __init__(self):
        self._cmdlets = {}

    def register(self, name):
        def decorator(fn):
            self._cmdlets[name] = fn
            return fn
        return decorator

    def get(self, name):
        if name not in self._cmdlets:
            raise KeyError(f'cmdlet not found: {name}')
        return self._cmdlets[name]

    def names(self):
        return list(self._cmdlets)


cmdlets = CmdletRegistry()

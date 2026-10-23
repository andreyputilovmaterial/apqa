

from dataclasses import dataclass, field, fields, asdict


@dataclass
class Rule:
    """A single QC rule.

    ``left`` and ``right`` are lists of cmdlet mappings::

        {'cmdlet': <name>, 'args': {<param>: <value>, ...}}

    ``op`` is the name of a registered comparison op (always scalar vs scalar).
    ``meta`` is an extensible bag of descriptive fields
    (created_by, created_at, comment, tags, markers, ...). ``meta.markers`` may
    carry pytest modifiers: ``skip`` (do not run the rule) or ``xfail``
    (a failure is expected and treated as normal).

    Only ``name`` is strictly required; the other fields default to empty values
    so that a rule can be created incrementally in the ui. Validation of the
    *meaning* of a rule is done by the comparison op at run time, not here.
    """

    name: str
    meta: dict = field(default_factory=dict)
    left: list = field(default_factory=list)
    op: str = ''
    right: list = field(default_factory=list)

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict):
            raise ValueError(f'rule must be a mapping, got {type(data).__name__}')
        name = data.get('name')
        if name is None or name == '':
            raise ValueError('rule is missing a name')
        name = f'{name}'

        meta = data.get('meta') or {}
        if not isinstance(meta, dict):
            raise ValueError(f'rule {name!r}: meta must be a mapping')

        left = data.get('left') or []
        if not isinstance(left, list):
            raise ValueError(f'rule {name!r}: left must be a list')

        right = data.get('right') or []
        if not isinstance(right, list):
            raise ValueError(f'rule {name!r}: right must be a list')

        op = data.get('op') or ''
        op = f'{op}'

        return cls(name=name, meta=meta, left=left, op=op, right=right)

    def run(self):
        """Execution entry point.

        Implemented once the cmdlet registry and comparison ops are in place.
        """
        raise NotImplementedError('rule execution is not implemented yet')

    def update(self, **changes):
        unknown = set(changes) - {f.name for f in fields(self)}
        if unknown:
            raise ValueError(
                f'unknown rule field(s): {", ".join(sorted(unknown))}'
            )
        for key, value in changes.items():
            setattr(self, key, value)
        return self

    def to_dict(self):
        return asdict(self)

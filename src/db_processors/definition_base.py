
from dataclasses import dataclass, field, fields, asdict


@dataclass
class Definition:
    """A single project-level definition (alias).

    A definition binds a short ``name`` to a reusable ``value`` (typically a file
    path), so that rules can reference e.g. ``PROCESSED_DATA`` instead of
    repeating a long path in every cmdlet argument. ``meta`` is an extensible bag
    of descriptive fields (comment, created_at, ...), just like a rule's ``meta``.

    Only ``name`` is strictly required; ``value`` defaults to an empty string so a
    definition can be created incrementally in the ui.
    """

    name: str
    value: str = ''
    meta: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict):
            raise ValueError(f'definition must be a mapping, got {type(data).__name__}')
        name = data.get('name')
        if name is None or name == '':
            raise ValueError('definition is missing a name')
        name = f'{name}'

        value = data.get('value') or ''
        value = f'{value}'

        meta = data.get('meta') or {}
        if not isinstance(meta, dict):
            raise ValueError(f'definition {name!r}: meta must be a mapping')

        return cls(name=name, value=value, meta=meta)

    def update(self, **changes):
        unknown = set(changes) - {f.name for f in fields(self)}
        if unknown:
            raise ValueError(
                f'unknown definition field(s): {", ".join(sorted(unknown))}'
            )
        for key, value in changes.items():
            setattr(self, key, value)
        return self

    def to_dict(self):
        return asdict(self)

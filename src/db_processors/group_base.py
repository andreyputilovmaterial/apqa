

from dataclasses import dataclass, field, fields, asdict


@dataclass
class Group:
    """A single folder/group of QC rules.

    Groups form a tree: ``parent`` is the name of the parent group, or an empty
    string for a top-level (root) group. ``name`` is the unique identity used by
    rules (``Rule.group``) and by child groups (``Group.parent``) to reference
    this group. ``meta`` is an extensible bag of descriptive fields, just like a
    rule's ``meta``.

    Only ``name`` is strictly required; ``parent`` defaults to an empty string
    (top level) and ``meta`` to an empty mapping so a group can be created
    incrementally in the ui.
    """

    name: str
    parent: str = ''
    meta: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict):
            raise ValueError(f'group must be a mapping, got {type(data).__name__}')
        name = data.get('name')
        if name is None or name == '':
            raise ValueError('group is missing a name')
        name = f'{name}'

        parent = data.get('parent') or ''
        parent = f'{parent}'

        meta = data.get('meta') or {}
        if not isinstance(meta, dict):
            raise ValueError(f'group {name!r}: meta must be a mapping')

        return cls(name=name, parent=parent, meta=meta)

    def update(self, **changes):
        unknown = set(changes) - {f.name for f in fields(self)}
        if unknown:
            raise ValueError(
                f'unknown group field(s): {", ".join(sorted(unknown))}'
            )
        for key, value in changes.items():
            setattr(self, key, value)
        return self

    def to_dict(self):
        return asdict(self)

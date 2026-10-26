

from dataclasses import dataclass, field, fields, asdict


def normalize_aliases(aliases):
    """Validate and normalize a group's alias list.

    Each alias is ``{'name': <str>, 'chain': [<cmdlet>, ...], 'meta': {...}}``.
    ``name`` is required and must be unique within the group; ``chain`` is a list
    of cmdlet mappings (validated at run time, not here); ``meta`` is optional.
    """
    if aliases is None:
        return []
    if not isinstance(aliases, list):
        raise ValueError(
            f'group aliases must be a list, got {type(aliases).__name__}'
        )
    normalized = []
    seen = set()
    for item in aliases:
        if not isinstance(item, dict):
            raise ValueError(
                f'group alias must be a mapping, got {type(item).__name__}'
            )
        name = item.get('name')
        if name is None or name == '':
            raise ValueError('group alias is missing a name')
        name = f'{name}'
        if name in seen:
            raise ValueError(f'group alias duplicated name: {name}')
        chain = item.get('chain') or []
        if not isinstance(chain, list):
            raise ValueError(f'group alias {name!r}: chain must be a list')
        meta = item.get('meta') or {}
        if not isinstance(meta, dict):
            raise ValueError(f'group alias {name!r}: meta must be a mapping')
        normalized.append({'name': name, 'chain': chain, 'meta': meta})
        seen.add(name)
    return normalized


@dataclass
class Group:
    """A single folder/group of QC rules.

    Groups form a tree: ``parent`` is the name of the parent group, or an empty
    string for a top-level (root) group. ``name`` is the unique identity used by
    rules (``Rule.group``) and by child groups (``Group.parent``) to reference
    this group. ``aliases`` is a list of ``{ name, chain, meta }`` entries that
    define folder-local reusable values (resolved once per folder at run time and
    inherited by sub-folders). ``meta`` is an extensible bag of descriptive
    fields, just like a rule's ``meta``.

    Only ``name`` is strictly required; ``parent`` defaults to an empty string
    (top level) and ``meta`` to an empty mapping so a group can be created
    incrementally in the ui.
    """

    name: str
    parent: str = ''
    aliases: list = field(default_factory=list)
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

        aliases = normalize_aliases(data.get('aliases'))

        return cls(name=name, parent=parent, aliases=aliases, meta=meta)

    def update(self, **changes):
        unknown = set(changes) - {f.name for f in fields(self)}
        if unknown:
            raise ValueError(
                f'unknown group field(s): {", ".join(sorted(unknown))}'
            )
        for key, value in changes.items():
            if key == 'aliases':
                value = normalize_aliases(value)
            setattr(self, key, value)
        return self

    def to_dict(self):
        return asdict(self)

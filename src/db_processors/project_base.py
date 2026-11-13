
from dataclasses import dataclass, field, fields, asdict


@dataclass
class Project:
    """Project-level metadata stored in the rules database file.

    A QC-rules database file describes one project. Besides the rule and group
    collections, the file carries a single project record:

    - ``name``    — free-form, user-visible project name
    - ``comment`` — short human-readable note about the project
    - ``meta``    — extensible bag of any other project-level info
      (created_by, created_at, tags, markers, ...)

    Unlike rules and groups, a project is a singleton (one per file) and has no
    technical id: the file path itself is the project's identity. All three
    fields default to empty values so a project can be described incrementally
    in the UI.
    """

    name: str = ''
    comment: str = ''
    meta: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data):
        if data is None:
            return cls()
        if not isinstance(data, dict):
            raise ValueError(f'project must be a mapping, got {type(data).__name__}')

        name = data.get('name') or ''
        comment = data.get('comment') or ''
        meta = data.get('meta') or {}

        name = f'{name}'
        comment = f'{comment}'
        if not isinstance(meta, dict):
            raise ValueError('project: meta must be a mapping')

        return cls(name=name, comment=comment, meta=meta)

    def update(self, **changes):
        unknown = set(changes) - {f.name for f in fields(self)}
        if unknown:
            raise ValueError(
                f'unknown project field(s): {", ".join(sorted(unknown))}'
            )
        for key, value in changes.items():
            setattr(self, key, value)
        return self

    def to_dict(self):
        return asdict(self)

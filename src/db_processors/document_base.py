

from .dbfile_base import DBFile as DBFileBase
from .group_base import Group
from .ids import ensure_unique
from .project_base import Project
from .rule_base import Rule


class DBFileDocument(DBFileBase):
    """In-memory document store shared by the file- and HTTP-backed processors.

    A "document" is the whole database serialized as one mapping::

        {'project': {...}, 'groups': [...], 'rules': [...]}

    Subclasses only implement the transport — how to load a document on open
    (``_read``) and how to persist it on ``save`` — plus ``_init_storage``. All
    CRUD lives here and mutates the in-memory ``_rules``/``_groups``/``_project``.
    """

    def __init__(self, resource_path):
        super().__init__(resource_path)
        self._rules = {}
        self._groups = {}
        self._project = Project()

    def _read_document(self, data):
        """Replace the in-memory state from a document mapping (or legacy list)."""
        # Backward-compatible: an older document is a top-level list of rules.
        if isinstance(data, list):
            data = {'rules': data}
        if not isinstance(data, dict):
            raise ValueError(
                f'db file: top-level must be a mapping or a list of rules: {self.resource_path}'
            )

        rules = data.get('rules') or []
        groups = data.get('groups') or []
        if not isinstance(rules, list):
            raise ValueError(f'db file: rules must be a list: {self.resource_path}')
        if not isinstance(groups, list):
            raise ValueError(f'db file: groups must be a list: {self.resource_path}')

        self._rules.clear()
        self._groups.clear()
        self._project = Project.from_dict(data.get('project'))
        for item in groups:
            group = Group.from_dict(item)
            if group.id in self._groups:
                raise ValueError(f'db file: duplicated group id(s): {group.id}')
            self._groups[group.id] = group
        # Resolve old-style (name) references to ids now that every group exists.
        for group in self._groups.values():
            group.parent = self.resolve_group_ref(group.parent)
        for item in rules:
            rule = Rule.from_dict(item)
            if rule.id in self._rules:
                raise ValueError(f'db file: duplicated rule id(s): {rule.id}')
            rule.group = self.resolve_group_ref(rule.group)
            self._rules[rule.id] = rule
        return self._rules

    def _to_document(self):
        return {
            'project': self._project.to_dict(),
            'groups': [group.to_dict() for group in self.list_groups()],
            'rules': [rule.to_dict() for rule in self.list_rules()],
        }

    # ---- CRUD -------------------------------------------------------------

    def list_rules(self):
        return [ rule for _,rule in self._rules.items() ]

    def get_rule(self, rule_id):
        rule_id = f'{rule_id}'
        if rule_id not in self._rules:
            raise KeyError(f'rule not found: {rule_id}')
        return self._rules[rule_id]

    def has_rule(self, rule_id):
        return f'{rule_id}' in self._rules

    def add_rule(self, rule):
        if not isinstance(rule, Rule):
            rule = Rule.from_dict(rule)
        self._ensure_rule_id_available(rule)
        rule.group = self.resolve_group_ref(rule.group)
        self._rules[rule.id] = rule
        return rule

    def update_rule(self, rule_id, **changes):
        # note: `rule_id` cannot be passed as a keyword here (Python raises
        # TypeError) — a rule's id is stable and cannot be changed.
        if 'id' in changes:
            raise ValueError("a rule's id cannot be changed")
        rule = self.get_rule(rule_id)
        rule.update(**changes)
        rule.group = self.resolve_group_ref(rule.group)
        return rule

    def rename_rule(self, rule_id, new_name):
        rule = self.get_rule(rule_id)
        rule.name = f'{new_name}'
        return rule

    def delete_rule(self, rule_id):
        rule = self.get_rule(rule_id)
        del self._rules[rule_id]
        return rule

    # ---- groups CRUD -----------------------------------------------------------

    def list_groups(self):
        return [ group for _,group in self._groups.items() ]

    def get_group(self, group_id):
        group_id = f'{group_id}'
        if group_id not in self._groups:
            raise KeyError(f'group not found: {group_id}')
        return self._groups[group_id]

    def has_group(self, group_id):
        return f'{group_id}' in self._groups

    def add_group(self, group):
        if not isinstance(group, Group):
            group = Group.from_dict(group)
        group.id = ensure_unique(group.id, self._existing_group_ids())
        group.parent = self._validate_group_parent(group, group.parent)
        self._groups[group.id] = group
        return group

    def update_group(self, group_id, **changes):
        # note: `group_id` cannot be passed as a keyword here (Python raises
        # TypeError) — a group's id is stable and cannot be changed.
        if 'id' in changes:
            raise ValueError("a group's id cannot be changed")
        group = self.get_group(group_id)
        group.update(**changes)
        group.parent = self._validate_group_parent(group, group.parent)
        return group

    def rename_group(self, group_id, new_name):
        group = self.get_group(group_id)
        group.name = f'{new_name}'
        return group

    def delete_group(self, group_id):
        group = self.get_group(group_id)
        if any(g.parent == group_id for g in self._groups.values()):
            raise ValueError(f'group is not empty (it has sub-groups): {group_id}')
        if any(r.group == group_id for r in self._rules.values()):
            raise ValueError(f'group is not empty (it has rules): {group_id}')
        del self._groups[group_id]
        return group

    # ---- project CRUD ----------------------------------------------------------

    def get_project(self):
        return self._project

    def update_project(self, **changes):
        self._project.update(**changes)
        return self._project

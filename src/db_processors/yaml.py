

from pathlib import Path
import yaml

from .dbfile_base import DBFile as DBFileBase
from .group_base import Group
from .rule_base import Rule


class IndexedProperty:
    def __init__(self, getter, setter=None):
        self.getter = getter
        self.setter_func = setter

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return _IndexedValue(instance, self.getter, self.setter_func)
    
    def setter(self, setter_func):
        return type(self)(self.getter, setter_func)

class _IndexedValue:
    def __init__(self, instance, getter, setter):
        self.instance = instance
        self.getter = getter
        self.setter = setter

    def __getitem__(self, key):
        return self.getter(self.instance, key)

    def __setitem__(self, key, value):
        if self.setter is None:
            raise AttributeError("can't set indexed property")
        self.setter(self.instance, key, value)



@DBFileBase.register('yaml')
class DBFileYaml(DBFileBase):
    def __init__(self,resource_path):
        self.resource_path = Path(resource_path).resolve()
        if not self.resource_path.is_file():
            raise FileNotFoundError(f'db file: file not found: {self.resource_path}')
        self._rules = {}
        self._groups = {}
        self._read()

    def _read(self):
        with open(self.resource_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        # Backward-compatible: an older file is a top-level list of rules.
        if isinstance(data, list):
            data = {'rules': data}
        if not isinstance(data, dict):
            raise ValueError(f'db file: top-level must be a mapping or a list of rules: {self.resource_path}')

        rules = data.get('rules') or []
        groups = data.get('groups') or []
        if not isinstance(rules, list):
            raise ValueError(f'db file: rules must be a list: {self.resource_path}')
        if not isinstance(groups, list):
            raise ValueError(f'db file: groups must be a list: {self.resource_path}')

        self._rules.clear()
        self._groups.clear()
        for item in rules:
            rule = Rule.from_dict(item)
            if rule.name in self._rules:
                raise ValueError(f'db file: duplicated rule name(s): {rule.name}')
            self._rules[rule.name] = rule
        for item in groups:
            group = Group.from_dict(item)
            if group.name in self._groups:
                raise ValueError(f'db file: duplicated group name(s): {group.name}')
            self._groups[group.name] = group
        return self._rules

    def save(self):
        with open(self.resource_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(
                {
                    'groups': [ group.to_dict() for group in self.list_groups() ],
                    'rules': [ rule.to_dict() for rule in self.list_rules() ],
                },
                f,
                sort_keys=False,
            )

    # ---- CRUD -------------------------------------------------------------

    def list_rules(self):
        return [ rule for _,rule in self._rules.items() ]

    def get_rule(self,name):
        name = f'{name}'
        if name not in self._rules:
            raise KeyError(f'rule not found: {name}')
        return self._rules[name]

    def has_rule(self,name):
        return f'{name}' in self._rules

    def add_rule(self,rule):
        if not isinstance(rule, Rule):
            rule = Rule.from_dict(rule)
        if rule.name in self._rules:
            raise ValueError(f'rule already exists: {rule.name}')
        self._rules[rule.name] = rule
        return rule

    def update_rule(self,name,**changes):
        # note: `name` cannot be passed as a keyword here (Python raises
        # TypeError) — renames go through rename_rule().
        rule = self.get_rule(name)
        rule.update(**changes)
        return rule

    def rename_rule(self,name,new_name):
        rule = self.get_rule(name)
        new_name = f'{new_name}'
        if new_name == name:
            return rule
        if new_name in self._rules:
            raise ValueError(f'rule already exists: {new_name}')
        del self._rules[name]
        rule.name = new_name
        self._rules[new_name] = rule
        return rule

    def delete_rule(self,name):
        rule = self.get_rule(name)
        del self._rules[name]
        return rule

    # ---- groups CRUD -----------------------------------------------------------

    def list_groups(self):
        return [ group for _,group in self._groups.items() ]

    def get_group(self,name):
        name = f'{name}'
        if name not in self._groups:
            raise KeyError(f'group not found: {name}')
        return self._groups[name]

    def has_group(self,name):
        return f'{name}' in self._groups

    def add_group(self,group):
        if not isinstance(group, Group):
            group = Group.from_dict(group)
        if group.name in self._groups:
            raise ValueError(f'group already exists: {group.name}')
        group.parent = self._validate_group_parent(group.name, group.parent)
        self._groups[group.name] = group
        return group

    def update_group(self,name,**changes):
        # note: `name` cannot be passed as a keyword here (Python raises
        # TypeError) — renames go through rename_group().
        group = self.get_group(name)
        group.update(**changes)
        group.parent = self._validate_group_parent(name, group.parent)
        return group

    def rename_group(self,name,new_name):
        group = self.get_group(name)
        new_name = f'{new_name}'
        if new_name == name:
            return group
        if new_name in self._groups:
            raise ValueError(f'group already exists: {new_name}')
        del self._groups[name]
        group.name = new_name
        self._groups[new_name] = group
        for child in self._groups.values():
            if child.parent == name:
                child.parent = new_name
        for rule in self._rules.values():
            if rule.group == name:
                rule.group = new_name
        return group

    def delete_group(self,name):
        group = self.get_group(name)
        if any(g.parent == name for g in self._groups.values()):
            raise ValueError(f'group is not empty (it has sub-groups): {name}')
        if any(r.group == name for r in self._rules.values()):
            raise ValueError(f'group is not empty (it has rules): {name}')
        del self._groups[name]
        return group

    # ---- backward-compatible accessors --------------------------------------
    # (the generic `.rules` accessor lives on the base class)

    @IndexedProperty
    def rule(self, name):
        return self.get_rule(name)

    @rule.setter
    def rule(self, name, value):
        if not isinstance(value, Rule):
            value = Rule.from_dict(value)
        self._rules[name] = value


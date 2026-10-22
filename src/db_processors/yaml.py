

from pathlib import Path
import yaml

from .dbfile_base import DBFile as DBFileBase
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
        self._read()

    def _read(self):
        with open(self.resource_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or []
        if not isinstance(data, list):
            raise ValueError(f'db file: top-level must be a list of rules: {self.resource_path}')
        self._rules.clear()
        for item in data:
            rule = Rule.from_dict(item)
            if rule.name in self._rules:
                raise ValueError(f'db file: duplicated rule name(s): {rule.name}')
            self._rules[rule.name] = rule
        return self._rules

    def save(self):
        with open(self.resource_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(
                [ rule.to_dict() for rule in self.list_rules() ],
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


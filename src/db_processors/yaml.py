

from pathlib import Path
import yaml

from .dbfile_base import DBFile as DBFileBase
from .definition_base import Definition
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
        self._definitions = {}
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
        definitions = data.get('definitions') or []
        if not isinstance(rules, list):
            raise ValueError(f'db file: rules must be a list: {self.resource_path}')
        if not isinstance(definitions, list):
            raise ValueError(f'db file: definitions must be a list: {self.resource_path}')

        self._rules.clear()
        self._definitions.clear()
        for item in rules:
            rule = Rule.from_dict(item)
            if rule.name in self._rules:
                raise ValueError(f'db file: duplicated rule name(s): {rule.name}')
            self._rules[rule.name] = rule
        for item in definitions:
            definition = Definition.from_dict(item)
            if definition.name in self._definitions:
                raise ValueError(f'db file: duplicated definition name(s): {definition.name}')
            self._definitions[definition.name] = definition
        return self._rules

    def save(self):
        with open(self.resource_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(
                {
                    'definitions': [ definition.to_dict() for definition in self.list_definitions() ],
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

    # ---- definitions CRUD ---------------------------------------------------

    def list_definitions(self):
        return [ definition for _,definition in self._definitions.items() ]

    def get_definition(self,name):
        name = f'{name}'
        if name not in self._definitions:
            raise KeyError(f'definition not found: {name}')
        return self._definitions[name]

    def has_definition(self,name):
        return f'{name}' in self._definitions

    def add_definition(self,definition):
        if not isinstance(definition, Definition):
            definition = Definition.from_dict(definition)
        if definition.name in self._definitions:
            raise ValueError(f'definition already exists: {definition.name}')
        self._definitions[definition.name] = definition
        return definition

    def update_definition(self,name,**changes):
        # note: `name` cannot be passed as a keyword here (Python raises
        # TypeError) — renames go through rename_definition().
        definition = self.get_definition(name)
        definition.update(**changes)
        return definition

    def rename_definition(self,name,new_name):
        definition = self.get_definition(name)
        new_name = f'{new_name}'
        if new_name == name:
            return definition
        if new_name in self._definitions:
            raise ValueError(f'definition already exists: {new_name}')
        del self._definitions[name]
        definition.name = new_name
        self._definitions[new_name] = definition
        return definition

    def delete_definition(self,name):
        definition = self.get_definition(name)
        del self._definitions[name]
        return definition

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


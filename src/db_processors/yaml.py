

from pathlib import Path
import yaml
from dataclasses import asdict

from .dbfile_base import DBFile as DBFileBase
from .rule_base import make_rule_factory




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
        def read():
            with open(self.resource_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or []
                rules_old = { rule.name: rule for _,rule in self._rules.items() }
                self._rules.clear()

                names_used = set()
                for rule in data:
                    rule_name = rule.get('name')
                    if not rule_name:
                        raise Exception(f'reading dbfile: a rule is missing a name')
                    if rule_name in names_used:
                        raise Exception(f'reading dbfile: duplicated rule name(s): {rule_name}')
                    names_used.add(rule_name)
                    if rule_name in rules_old:
                        rule_existing = rules_old[rule_name]
                        rule_existing.update(rule)
                        rule_obj = rule_existing
                    else:
                        RuleCls = self._Rule
                        rule_obj = RuleCls(rule)
                    self._rules[rule_name] = rule_obj
                return self._rules
        def save():
            with open(self._path, "w", encoding="utf-8") as f:
                yaml.safe_dump([ asdict(rule) for _,rule in self._rules.items() ], f, sort_keys=False)
        self._save = save
        self._Rule = make_rule_factory(read,save)
        self._rules = {}
        read()

    @property
    def rules(self) -> str:
        return [ rule for _,rule in self._rules.items() ]

    @IndexedProperty
    def rule(self, name):
        return self._rules[name]

    @rule.setter
    def rule(self, name, value):
        self._rules[name] = value


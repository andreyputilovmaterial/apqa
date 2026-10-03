

from pathlib import Path
import yaml
from dataclasses import asdict

from .dbfile_base import DBFile as DBFileBase
from .rule_base import make_rule_factory


@DBFileBase.register('yaml')
class DBFileYaml(DBFileBase):
    def __init__(self,resource_path):
        self.resource_path = Path(resource_path).resolve()
        if not self.resource_path.is_file():
            raise FileNotFoundError(f'db file: file not found: {self.resource_path}')
        def read():
            with open(self.resource_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or []
                rules_old = [ rule for rule in self._rules ]
                rules_old_as_dict = { rule.name: rule for rule in rules_old }

                rules_updated = [ self.Rule(record) if record.get('name') not in rules_old_as_dict else rules_old_as_dict[record.get('name')].update(record) for record in data ]
                rules_names = [ rule.name for rule in rules_updated ]
                is_unique = len(set(rules_names)) == len(rules_names)
                if not is_unique:
                    raise Exception(f'reading dbfile: duplicated rule name(s): {[ rule_name for rule_name in rules_names if len([n for n in rules_names if n==rule_name])>1 ]}')
                del self._rules[:]
                names_used = set()
                for rule in data:
                    rule_name = rule.get('name')
                    if not rule_name:
                        raise Exception(f'reading dbfile: a rule is missing a name')
                    if rule_name in names_used:
                        raise Exception(f'reading dbfile: duplicated rule name(s): {rule_name}')
                    names_used.add(rule_name)
                    if rule_name in rules_old_as_dict:
                        rule_existing = rules_old_as_dict[rule_name]
                        rule_existing.update(rule)
                        rule_obj = rule_existing
                    else:
                        rule_obj = self._Rule(rule)
                    self._rules.append(rule_obj)
                return self._rules
        def save():
            with open(self._path, "w", encoding="utf-8") as f:
                yaml.safe_dump([ asdict(rule) for rule in self._rules ], f, sort_keys=False)
        self._save = save
        self._Rule = make_rule_factory(read,save)
        self._rules = []
        read()

    @property
    def name(self) -> str:
        return self._data.get("name", "")

    @name.setter
    def name(self, value: str):
        self._data["name"] = value
        self._save()


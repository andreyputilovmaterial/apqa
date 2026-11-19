

from pathlib import Path

from ..dbfile_base import DBFile as DBFileBase
from ..document_base import DBFileDocument
from ..rule_base import Rule


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
class DBFileYaml(DBFileDocument):
    def __init__(self,resource_path):
        resource_path = Path(resource_path).resolve()
        super().__init__(resource_path)
        if not self.resource_path.is_file():
            raise FileNotFoundError(f'db file: file not found: {self.resource_path}')
        self._read()

    @classmethod
    def _init_storage(cls, resource_path):
        import yaml  # lazy: PyYAML is only needed for the YAML backend
        path = Path(resource_path).resolve()
        if path.exists():
            raise FileExistsError(f'db file: already exists: {path}')
        with open(path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(
                {
                    'project': {'name': '', 'comment': '', 'meta': {}},
                    'groups': [],
                    'rules': [],
                },
                f,
                sort_keys=False,
            )
        return path

    def _read(self):
        import yaml  # lazy: PyYAML is only needed for the YAML backend
        with open(self.resource_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        self._read_document(data)

    def save(self):
        import yaml  # lazy: PyYAML is only needed for the YAML backend
        with open(self.resource_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(self._to_document(), f, sort_keys=False)

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


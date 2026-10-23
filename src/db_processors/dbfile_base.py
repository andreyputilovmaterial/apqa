
from .detect_type import detect_type


class DBFile:
    """Format-agnostic interface to a project's QC-rules database file.

    Subclasses register themselves via ``DBFile.register('<type>')`` keyed by
    the resource type returned from :func:`detect_type` (e.g. 'yaml', 'json').
    """

    def __new__(cls,resource_path):
        def detect_dbfile_cls(dbfile_processors,resource_path):
            resource_type = detect_type(resource_path)
            if resource_type in dbfile_processors:
                return dbfile_processors[resource_type]
            else:
                raise NotImplementedError(f'db file: resource type not supported: {resource_type or "unrecognized"}')
        if cls is DBFile:
            DBFileCls = detect_dbfile_cls(cls._registry,resource_path)
            return DBFileCls(resource_path)
        return super().__new__(cls)

    _registry = {}

    @classmethod
    def register(cls,name):
        def decorator(dbfile_cls):
            cls._registry[name] = dbfile_cls
            return dbfile_cls
        return decorator

    def __init__(self,resource_path):
        self.resource_path = resource_path

    # ---- CRUD contract ---------------------------------------------------
    # Subclasses implement these. The defaults raise so that a missing
    # implementation fails loudly rather than silently doing nothing.

    def list_rules(self):
        raise NotImplementedError

    def get_rule(self,name):
        raise NotImplementedError

    def has_rule(self,name):
        raise NotImplementedError

    def add_rule(self,rule):
        raise NotImplementedError

    def update_rule(self,name,**changes):
        raise NotImplementedError

    def rename_rule(self,name,new_name):
        raise NotImplementedError

    def delete_rule(self,name):
        raise NotImplementedError

    def save(self):
        raise NotImplementedError

    # ---- definitions CRUD contract -----------------------------------------
    # Definitions (aliases) are stored in the same database file as the rules.
    # They give a short name to a reusable value (e.g. a path) so rules can
    # reference the name instead of repeating the value.

    def list_definitions(self):
        raise NotImplementedError

    def get_definition(self,name):
        raise NotImplementedError

    def has_definition(self,name):
        raise NotImplementedError

    def add_definition(self,definition):
        raise NotImplementedError

    def update_definition(self,name,**changes):
        raise NotImplementedError

    def rename_definition(self,name,new_name):
        raise NotImplementedError

    def delete_definition(self,name):
        raise NotImplementedError

    # ---- pythonic helpers -------------------------------------------------

    def __len__(self):
        return len(self.list_rules())

    def __iter__(self):
        return iter(self.list_rules())

    def __contains__(self,name):
        return self.has_rule(name)

    # ---- backward-compatible accessors --------------------------------------

    @property
    def rules(self):
        return self.list_rules()

    @property
    def definitions(self):
        return self.list_definitions()




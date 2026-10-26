
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

    # ---- groups CRUD contract -----------------------------------------------
    # Groups (folders) organize rules into a foldable tree. A group references
    # its parent by name ('' = top level); rules reference their group via
    # ``Rule.group``. Renaming a group cascades to its rules and child groups;
    # deleting a group is refused while it still contains rules or sub-groups.

    def list_groups(self):
        raise NotImplementedError

    def get_group(self,name):
        raise NotImplementedError

    def has_group(self,name):
        raise NotImplementedError

    def add_group(self,group):
        raise NotImplementedError

    def update_group(self,name,**changes):
        raise NotImplementedError

    def rename_group(self,name,new_name):
        raise NotImplementedError

    def delete_group(self,name):
        raise NotImplementedError

    def _validate_group_parent(self, name, parent):
        """Return the canonical parent name, or raise on an invalid reference.

        Rejects a missing parent, a group being its own parent, and any parent
        chain that would close a cycle back onto ``name``. Used by the storage
        backends before adding/updating a group so the tree stays a forest.
        """
        parent = f'{parent}' if parent is not None else ''
        if parent == '':
            return ''
        if parent == name:
            raise ValueError(f'group {name!r} cannot be its own parent')
        if not self.has_group(parent):
            raise ValueError(f'group parent not found: {parent}')
        seen = set()
        cursor = parent
        while cursor:
            if cursor in seen:
                raise ValueError(
                    f'group parent chain contains a cycle at {cursor!r}'
                )
            seen.add(cursor)
            if cursor == name:
                raise ValueError(
                    f'group {name!r} cannot be nested under its own descendant {parent!r}'
                )
            cursor = self.get_group(cursor).parent
        return parent

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
    def groups(self):
        return self.list_groups()




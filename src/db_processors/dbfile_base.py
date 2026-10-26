
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

    def get_rule(self, rule_id):
        raise NotImplementedError

    def has_rule(self, rule_id):
        raise NotImplementedError

    def add_rule(self, rule):
        raise NotImplementedError

    def update_rule(self, rule_id, **changes):
        raise NotImplementedError

    def rename_rule(self, rule_id, new_name):
        raise NotImplementedError

    def delete_rule(self, rule_id):
        raise NotImplementedError

    def save(self):
        raise NotImplementedError

    # ---- groups CRUD contract -----------------------------------------------
    # Groups (folders) organize rules into a foldable tree. A group references
    # its parent by id ('' = top level); rules reference their group via
    # ``Rule.group`` (a group id). ``resolve_group_ref`` accepts either an id or
    # a display name so data written before the id/name split still loads.
    # Deleting a group is refused while it still contains rules or sub-groups.

    def list_groups(self):
        raise NotImplementedError

    def get_group(self, group_id):
        raise NotImplementedError

    def has_group(self, group_id):
        raise NotImplementedError

    def add_group(self, group):
        raise NotImplementedError

    def update_group(self, group_id, **changes):
        raise NotImplementedError

    def rename_group(self, group_id, new_name):
        raise NotImplementedError

    def delete_group(self, group_id):
        raise NotImplementedError

    def resolve_group_ref(self, value):
        """Resolve a group reference to its id, accepting either an id or a display name.

        ``''``/``None`` mean "no group". An exact id wins over a display name, so
        a group whose display name happens to equal another group's id stays
        unambiguous. Raises ``ValueError`` when the reference matches nothing.
        """
        value = f'{value}' if value not in (None, '') else ''
        if value == '':
            return ''
        if self.has_group(value):
            return value
        for group in self.list_groups():
            if group.name == value:
                return group.id
        raise ValueError(f'group not found: {value}')

    def _existing_rule_ids(self):
        return {rule.id for rule in self.list_rules()}

    def _existing_group_ids(self):
        return {group.id for group in self.list_groups()}

    def _validate_group_parent(self, group, parent):
        """Return the canonical parent id, or raise on an invalid reference.

        Accepts the parent as either a group id or a display name (the latter for
        data written before the id/name split). Rejects a missing parent, a group
        being its own parent, and any parent chain that would close a cycle back
        onto ``group``. Used by the storage backends before adding/updating a
        group so the tree stays a forest.
        """
        parent = f'{parent}' if parent not in (None, '') else ''
        if parent == '':
            return ''
        if parent == group.id or parent == group.name:
            raise ValueError(f'group {group.name!r} cannot be its own parent')
        parent_id = self.resolve_group_ref(parent)
        seen = set()
        cursor = parent_id
        while cursor:
            if cursor in seen:
                raise ValueError(
                    f'group parent chain contains a cycle at {cursor!r}'
                )
            seen.add(cursor)
            if cursor == group.id:
                raise ValueError(
                    f'group {group.name!r} cannot be nested under its own descendant {parent!r}'
                )
            cursor = self.get_group(cursor).parent
        return parent_id

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




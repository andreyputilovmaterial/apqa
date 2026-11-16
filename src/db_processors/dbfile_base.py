
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
            # Allocate the concrete processor without invoking its __init__ here;
            # type.__call__ will then run DBFileCls.__init__ exactly once (that is
            # where a physical-file processor resolves its resource path).
            return object.__new__(DBFileCls)
        return super().__new__(cls)

    _registry = {}

    @classmethod
    def register(cls,name):
        def decorator(dbfile_cls):
            cls._registry[name] = dbfile_cls
            return dbfile_cls
        return decorator

    @classmethod
    def init_storage(cls, resource_path, resource_type=None):
        """Create an empty QC-rules storage at ``resource_path``.

        ``resource_type`` is the registry key of the storage format (e.g.
        ``'yaml'``, ``'sqlite'``). When omitted it is derived from the path via
        :func:`~.detect_type.detect_type`, the same logic used when opening a
        database. This method is only the router: the concrete creation logic
        lives in each registered processor's ``_init_storage`` classmethod, so
        the set of supported formats is whatever is currently registered, never
        a hardcoded list.
        """
        if resource_type is None:
            resource_type = detect_type(resource_path)
        processor_cls = cls._registry.get(resource_type)
        if processor_cls is None:
            raise NotImplementedError(
                f'db file: resource type not supported: {resource_type or "unrecognized"}'
            )
        return processor_cls._init_storage(resource_path)

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

    def _ensure_rule_id_available(self, rule):
        """Reject a rule whose ``id`` already exists.

        The id is the stable technical identity, so adding a rule that reuses an
        existing id is an error. (Auto-deduplication of a *generated* slug moved
        to the UI; the backend stays the authority and refuses a duplicate.)
        """
        if self.has_rule(rule.id):
            raise ValueError(f'rule with id already exists: {rule.id}')
        return rule

    def reorder(self, kind, item_id, parent='', before=None):
        """Move a rule or a group to a new position in the tree.

        ``kind`` is ``'rule'`` or ``'group'``; ``item_id`` is the moved item's id
        (unprefixed). ``parent`` is the **id** of the target folder/group, or
        ``''``/``None`` for the top level. ``before`` is the sibling the item is
        inserted *before*, encoded with a kind prefix to stay unambiguous across
        the rule/group id spaces (``r:<rule-id>`` / ``g:<group-id>``); ``None``/
        ``''`` appends at the end of ``parent``'s children.

        Sibling ordering is the same as the UI: within one parent, sub-folders and
        rules share one ``meta.order`` space (ties keep insertion order, sub-folders
        before rules). After the move, every sibling under the target parent is
        renumbered to consecutive integers (``0..n-1``) so the stored orders stay
        clean and drift-free. Only the target parent's children are touched.

        Returns the moved ``Rule``/``Group`` (its ``group``/``parent`` and
        ``meta.order`` are updated in place and persisted by the caller via
        :meth:`save`).
        """
        kind = f'{kind}'
        item_id = f'{item_id}'

        if kind not in ('rule', 'group'):
            raise ValueError(f"unknown kind: {kind!r}")

        parent = self.resolve_group_ref('' if parent in (None, '') else parent)

        if kind == 'rule':
            if not self.has_rule(item_id):
                raise KeyError(f'rule not found: {item_id}')
            item = self.get_rule(item_id)
            siblings = []
            for rule in self.list_rules():
                if rule.group == parent and rule.id != item_id:
                    siblings.append(('rule', rule))
            for group in self.list_groups():
                if group.parent == parent:
                    siblings.append(('group', group))
        else:
            if not self.has_group(item_id):
                raise KeyError(f'group not found: {item_id}')
            item = self.get_group(item_id)
            parent = self._validate_group_parent(item, parent)
            siblings = []
            for group in self.list_groups():
                if group.parent == parent and group.id != item_id:
                    siblings.append(('group', group))
            for rule in self.list_rules():
                if rule.group == parent:
                    siblings.append(('rule', rule))

        before_kind = None
        before_id = None
        if before not in (None, ''):
            before = f'{before}'
            if before.startswith('r:'):
                before_kind, before_id = 'rule', before[2:]
            elif before.startswith('g:'):
                before_kind, before_id = 'group', before[2:]
            else:
                raise ValueError(
                    f'invalid before reference: {before!r} '
                    f'(expected r:<id> or g:<id>)'
                )

        def order_of(obj):
            meta = obj.meta or {}
            value = meta.get('order')
            try:
                return float(value)
            except (TypeError, ValueError):
                return 0.0

        # Stable sort matching the UI tie-break: sub-folders before rules on an
        # equal order, insertion order within each kind.
        def sort_key(entry):
            entry_kind, obj = entry
            return (order_of(obj), 0 if entry_kind == 'group' else 1)

        ordered = sorted(siblings, key=sort_key)

        if before_id is not None:
            insert_at = None
            for index, (entry_kind, obj) in enumerate(ordered):
                if entry_kind == before_kind and obj.id == before_id:
                    insert_at = index
                    break
            if insert_at is None:
                raise ValueError(f'sibling not found under parent: {before!r}')
        else:
            insert_at = len(ordered)

        ordered.insert(insert_at, (kind, item))

        for position, (entry_kind, obj) in enumerate(ordered):
            meta = dict(obj.meta or {})
            meta['order'] = position
            if entry_kind == 'rule':
                if entry_kind == kind and obj.id == item_id:
                    self.update_rule(obj.id, meta=meta, group=parent)
                else:
                    self.update_rule(obj.id, meta=meta)
            else:
                if entry_kind == kind and obj.id == item_id:
                    self.update_group(obj.id, meta=meta, parent=parent)
                else:
                    self.update_group(obj.id, meta=meta)

        return item

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

    # ---- project contract -------------------------------------------------
    # A database file describes one project. Project-level metadata (name,
    # comment, and an extensible meta bag) is stored alongside the rules and
    # groups and returned as a :class:`~.project_base.Project`.

    def get_project(self):
        raise NotImplementedError

    def update_project(self, **changes):
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
    def groups(self):
        return self.list_groups()

    @property
    def project(self):
        return self.get_project()




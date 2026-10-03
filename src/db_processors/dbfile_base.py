
from .detect_type import detect_type


class DBFile:
    def __new__(cls,resource_path):
        def detect_dbfile_cls(dbfile_processors,resource_path):
            resource_type = detect_type(resource_path)
            if resource_type in dbfile_processors:
                return dbfile_processors[resource_type]
            else:
                raise NotImplementedError(f'db file: resource type not supported: {resource_type or 'unrecognized'}')
        if cls is DBFile:
            DBFileCls = detect_dbfile_cls(cls._registry,resource_path)
            return DBFileCls(resource_path)
        return super().__new__(cls)

    _registry = {}

    @classmethod
    def register(cls,name):
        def decorator(dbfile_cls):
            cls._registry[name] = dbfile_cls
        return decorator

    def __init__(self,resource_path):
        pass
    




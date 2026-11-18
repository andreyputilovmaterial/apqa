
from pathlib import Path
import re


def detect_type(resource_path: Path | str | None) -> str | None:
    def is_empty(val):
        if(isinstance(val,(str,int,float,bool,list,tuple,dict,set,))):
            return False
        else:
            return not val
    if is_empty(resource_path):
        return None
    resource_path = f'{resource_path}' # to make sure it's string
    # The scheme part of a SQLAlchemy URL is a dialect, optionally with a
    # ``+driver`` suffix (e.g. ``postgresql+psycopg2``), so it may contain
    # ``+``/``.``/``-`` in addition to letters and digits.
    protocol_str_matches = re.match(r'^([A-Za-z0-9_.+-]+)://(.*)$',resource_path,flags=re.I|re.DOTALL)
    if protocol_str_matches:
        str_protocol_part = protocol_str_matches[1].lower()
        # str_rest = protocol_str_matches[2]
        if str_protocol_part=='file':
            resource_path = Path(resource_path).resolve()
            if resource_path.suffix.lower() in ('.yaml','.yml',):
                return 'yaml'
            elif resource_path.suffix.lower() in ('.json',):
                return 'json'
            elif resource_path.suffix.lower() in ('.sqlite','.sqlite3',):
                return 'sqlite'
            else:
                return None
        # Any other scheme (postgresql://, mysql://, mssql+pyodbc://, oledb://,
        # …) is a SQLAlchemy URL. The SQLAlchemy processor validates it and
        # raises a readable error for schemes/dialects it doesn't know.
        return 'sqlalchemy'
    else:
        # I'd love to have better validation that path is a file, but can't think
        # of any good way to detect it - physical path can start with a slash, with
        # drive, a colon, and a backslashes (windows), with cnc network windows path...

        # No need to escape in the inside - it's not the full protocol string,
        # it's just a convention to pass path, with first part indicating connection type.
        return detect_type(f'file://{resource_path}')

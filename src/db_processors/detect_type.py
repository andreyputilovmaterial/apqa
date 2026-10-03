
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
    protocol_str_matches = re.match(r'^(\w+)://(.*)$',resource_path,flags=re.I|re.DOTALL)
    if protocol_str_matches:
        str_protocol_part = protocol_str_matches[1]
        # str_rest = protocol_str_matches[2]
        if str_protocol_part=='oledb':
            return 'oledb'
        return None
    else:
        resource_path = Path(resource_path).resolve()
        if resource_path.suffix.lower() in ('.yaml','.yml',):
            return 'yaml'
        elif resource_path.suffix.lower() in ('.json',):
            return 'json'
        else:
            return None


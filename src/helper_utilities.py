
import sys # for checking pinliner, and for verifying python ver
import re
from datetime import date
import yaml





def prettyprint_config(data):
    return yaml.dump(data,sort_keys=False)
    # txt = ''
    # for key, value in data.items():
    #     txt += f'{key}: {value}\n'





def is_in_pinliner():
    for p in sys.meta_path:
        try:
            cls_str = f'{(p.__class__)}'
            if re.match(r'.*\.InlinerImporter\b.*',cls_str):
                return True
        except:
            pass
    return False










def assess_python_ver():
    PYTHON_EOL = {
        (3, 9):  date(2025, 10, 31),
        (3, 10): date(2026, 10, 31),
        (3, 11): date(2027, 10, 31),
        (3, 12): date(2028, 10, 31),
        (3, 13): date(2029, 10, 31),
        (3, 14): date(2030, 10, 31),
    }
    version = sys.version_info[:2]
    result = {
        'python_version': f'{version[0]}.{version[1]}',
    }
    eol = PYTHON_EOL.get(version)
    if eol is not None:
        if date.today() >= eol:
            result['is_not_supported'] = True
    return result

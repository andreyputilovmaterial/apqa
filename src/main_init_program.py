

from datetime import datetime, timezone
import argparse


from .db_processors import DBFile
from .db_processors.detect_type import detect_type

from .GENERATED.VERSION import _VERSION as script_version
from .helper_utilities import prettyprint_config


script_version = f'{script_version}'.strip()

# STDOUT_COLOR_RED = "\033[91m"
STDOUT_COLOR_RED = "\033[31m"
STDOUT_COLOR_RESET = "\033[0m"
STDOUT_COLOR_GREEN = "\033[32m"


def main(*argcs,**kwargs):
    time_start = datetime.now(timezone.utc)
    script_name = 'apqa init script'

    parser = argparse.ArgumentParser(
        description="apqa_init"
    )
    parser.add_argument(
        #'-1',
        '--db-file',
        type=str,
        required=True,
        help='path of the new QC-rules storage to create (e.g. project.sqlite3 or project.yaml)',
    )
    parser.add_argument(
        '--db-format',
        type=str,
        required=False,
        default=None,
        help='storage format (e.g. yaml, sqlite); defaults to the format detected from --db-file',
    )
    args = parser.parse_args(*argcs,**kwargs)

    print(f'{STDOUT_COLOR_GREEN}starting {script_name} at {time_start}{STDOUT_COLOR_RESET}')

    if args.db_file:
        db_file = f'{args.db_file}' # make sure it's text
    else:
        raise Exception('db_file not specified')

    db_format = f'{args.db_format}' if args.db_format else None

    cfg_to_print_verify = {
        "db_file": db_file,
        "db_format": db_format if db_format is not None else detect_type(db_file),
    }
    print(f'CONFIG:\n{prettyprint_config(cfg_to_print_verify)}')
    print('\n')

    # Thin router: DBFile.init_storage dispatches to the init of the proper
    # registered db_processor. It supports every format currently registered in
    # src/db_processors — nothing is hardcoded here.
    created_path = DBFile.init_storage(db_file, db_format)

    print(f'{STDOUT_COLOR_GREEN}created {created_path}{STDOUT_COLOR_RESET}')
    return created_path

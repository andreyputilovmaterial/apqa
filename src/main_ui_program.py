

from datetime import datetime, timezone
import argparse
from pathlib import Path
from dotenv import load_dotenv # for loading .env
import os # for loading .env


from .webserver_engine.webserve.src.webserver import Webserver # a wrapper around python http.server - no flask or django
from .webserver_engine.webserve.src.webserver import HTTP403, HTTP404, WebResponse
from .webserver_engine.webserve.src.find_free_port import find_free_port
from .webserver_engine.webserve.src.launch_browser import launch_browser

from .db_processors import DBFile

from .GENERATED.VERSION import _VERSION as script_version
from .GENERATED.HELP import _MD as help_md
from .helper_utilities import (
    prettyprint_config,
    is_in_pinliner,
    assess_python_ver,
)

from .endpoints import endpoints

if is_in_pinliner():
    from .GENERATED.HARDCODED import _CREDENTIALS_STR as credentials_str
    credentials_str = credentials_str.strip()
else:
    load_dotenv()
    credentials_str = os.getenv("CREDENTIALS", "-")



CONFIG_WEBSERVER_MULTITHREADED = True
PORT_START_WITH = 5180


script_version = f'{script_version}'.strip()

# STDOUT_COLOR_RED = "\033[91m"
STDOUT_COLOR_RED = "\033[31m"
STDOUT_COLOR_RESET = "\033[0m"
STDOUT_COLOR_GREEN = "\033[32m"







def main(*argcs,**kwargs):
    time_start = datetime.now(timezone.utc)
    script_name = 'apqa ui script'

    parser = argparse.ArgumentParser(
        description="apqa_ui"
    )
    parser.add_argument(
        #'-1',
        '--db-file',
        type=str,
        required=True
    )
    args = parser.parse_args(*argcs,**kwargs)

    print(f'{STDOUT_COLOR_GREEN}starting {script_name} at {time_start}{STDOUT_COLOR_RESET}')
    config = {
        'time_start': time_start,
        'script_name': script_name,
        'script_version': script_version,
        'credentials:year': f'{datetime.now().year}',
        'credentials:name': credentials_str,
        'credentials:version': script_version,

        'help_pages': help_md,

        'db_file': None,

        'http_host': None,
        'http_port': None,
        'http_address': None,

        'app_config': {
            'is_webserver_multithreaded': CONFIG_WEBSERVER_MULTITHREADED,
        },

        'info': {},
        'warnings': [],

        'iface': {
            'WebResponse': WebResponse,
            'HTTP403': HTTP403,
            'HTTP404': HTTP404,
        },
    }

    verify_python_ver = assess_python_ver()
    config['info'].update(verify_python_ver)
    if verify_python_ver.get('is_not_supported'):
        config['warnings'].append(f'Warning: python {verify_python_ver.get("python_version")} is quite old and is beyond its EOL and is not receiving security updates. Please consider updating.')

    if args.db_file:
        db_file = f'{args.db_file}' # make sure it's text
        config['db_file'] = db_file
        config['iface']['db_file'] = DBFile(db_file)
    else:
        raise Exception('db_file not specified')

    print('\npreparing webserver...\n')
    config['http_host'] = 'localhost'
    config['http_port'] = find_free_port(config['http_host'], start=PORT_START_WITH)
    config['http_protocol'] = 'http'
    config['http_address'] = (
        f'{config["http_protocol"]}://'
        f'{config["http_host"]}:{config["http_port"]}'
    )

    cfg_to_print_verify = {
        "db_file":config.get("db_file"),
        "http_address":config.get("http_address"),
    }
    print(f'CONFIG:\n{prettyprint_config(cfg_to_print_verify)}')
    print('\n')
    server = Webserver(config,is_threading=CONFIG_WEBSERVER_MULTITHREADED) # a wrapper around python http.server - no flask or django
    server.assign_handlers(endpoints)
    # print(f'{STDOUT_COLOR_GREEN}starting webserver at {config.get("http_address")}{STDOUT_COLOR_RESET}')

    launch_browser(f'{config.get("http_address")}/')
    server.run()

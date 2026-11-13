

from datetime import datetime, timezone
import argparse
from pathlib import Path
from dotenv import load_dotenv # for loading .env
import os # for loading .env


# Entry-point module: import relatively (inside the `src` package / pinliner
# bundle) or flat (inlined with no parent package).
if __package__:
    from .webserver_engine.webserve.src.webserver import Webserver # a wrapper around python http.server - no flask or django
    from .webserver_engine.webserve.src.webserver import HTTP403, HTTP404, WebResponse
    from .webserver_config import select_webserver_port
    from .browser_launcher import (
        BROWSER_MODE_DEFAULT,
        BROWSER_MODE_NOOP,
        BROWSER_MODE_PYWEBVIEW,
        launch_browser_for_mode,
    )

    from .db_processors import DBFile

    from .GENERATED.VERSION import _VERSION as script_version
    from .GENERATED.HELP import _MD as help_md
    from .helper_utilities import (
        prettyprint_config,
        is_in_pinliner,
        assess_python_ver,
    )

    from .endpoints import endpoints
    from .rule_runner import run_rule
    from .cmdlets.meta import get_cmdlet_metadata
else:
    # flat context: inlined with no parent package.
    from webserver_engine.webserve.src.webserver import Webserver
    from webserver_engine.webserve.src.webserver import HTTP403, HTTP404, WebResponse
    from webserver_config import select_webserver_port
    from browser_launcher import (
        BROWSER_MODE_DEFAULT,
        BROWSER_MODE_NOOP,
        BROWSER_MODE_PYWEBVIEW,
        launch_browser_for_mode,
    )

    from db_processors import DBFile

    from GENERATED.VERSION import _VERSION as script_version
    from GENERATED.HELP import _MD as help_md
    from helper_utilities import (
        prettyprint_config,
        is_in_pinliner,
        assess_python_ver,
    )

    from endpoints import endpoints
    from rule_runner import run_rule
    from cmdlets.meta import get_cmdlet_metadata

if is_in_pinliner():
    from .GENERATED.HARDCODED import _CREDENTIALS_STR as credentials_str
    credentials_str = credentials_str.strip()
else:
    load_dotenv()
    credentials_str = os.getenv("CREDENTIALS", "-")



CONFIG_WEBSERVER_MULTITHREADED = True
# The default listen port (5280) and the `--config-webserver-port` options are
# handled in src/webserver_config.py. NOTE for developers: the Vite frontend dev
# server has 5280 pre-configured and hard-coded (vite.config.js proxies every
# API call to http://localhost:5280), so while developing against Vite keep the
# backend on 5280; without the dev frontend server any port works equally well.


script_version = f'{script_version}'.strip()

# STDOUT_COLOR_RED = "\033[91m"
STDOUT_COLOR_RED = "\033[31m"
STDOUT_COLOR_RESET = "\033[0m"
STDOUT_COLOR_GREEN = "\033[32m"







def get_help_pages():
    return help_md


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
    parser.add_argument(
        '--browser',
        choices=[BROWSER_MODE_DEFAULT, BROWSER_MODE_NOOP, BROWSER_MODE_PYWEBVIEW],
        default=BROWSER_MODE_DEFAULT,
        help=(
            'how to open the web UI: launch-system-default-browser (default, '
            'opens the OS default browser), no-op (start without a browser), '
            'pywebview (reserved, not implemented yet)'
        ),
    )
    parser.add_argument(
        '--config-webserver-port',
        type=str,
        default=None,
        help=(
            'backend listen port: a fixed port (fail if it is occupied), or '
            '"<port>+" to auto-increment by one until a free port is found; '
            'the default is auto-increment starting at 5280. NOTE: the Vite '
            'dev server hard-codes localhost:5280 as its proxy target, so keep '
            'the backend on 5280 while developing against it; without it any '
            'port works equally well.'
        ),
    )
    args = parser.parse_args(*argcs,**kwargs)

    # Fail early: pywebview is declared as an option but not implemented yet.
    if args.browser == BROWSER_MODE_PYWEBVIEW:
        raise NotImplementedError(
            f'--browser {BROWSER_MODE_PYWEBVIEW} is not implemented yet'
        )

    print(f'{STDOUT_COLOR_GREEN}starting {script_name} at {time_start}{STDOUT_COLOR_RESET}')
    config = {
        'time_start': time_start,
        'script_name': script_name,
        'script_version': script_version,
        'credentials:year': f'{datetime.now().year}',
        'credentials:name': credentials_str,
        'credentials:version': script_version,

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
            'get_help_pages': get_help_pages,
            'run_rule': run_rule,
            'get_cmdlet_metadata': get_cmdlet_metadata,
        },
    }

    verify_python_ver = assess_python_ver()
    config['info'].update(verify_python_ver)
    if verify_python_ver.get('is_not_supported'):
        config['warnings'].append(f'Warning: python {verify_python_ver.get("python_version")} is quite old and is beyond its EOL and is not receiving security updates. Please consider updating.')

    if args.db_file:
        db_file = f'{args.db_file}' # make sure it's text
        db_file_instance = DBFile(db_file)
        # Store the resolved path so every consumer (the page header and
        # GET /qc/project) serves the same string as db_file.resource_path.
        config['db_file'] = str(db_file_instance.resource_path)
        config['iface']['db_file'] = db_file_instance
    else:
        raise Exception('db_file not specified')

    print('\npreparing webserver...\n')
    config['http_host'] = 'localhost'
    config['http_port'] = select_webserver_port(config['http_host'], args.config_webserver_port)
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

    launch_browser_for_mode(args.browser, f'{config.get("http_address")}/')
    server.run()


if __name__ == '__main__':
    main()

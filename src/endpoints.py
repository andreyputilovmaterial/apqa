
import re
from functools import partial

from .frontend.endpoints import (
    render_page_home,
    render_page_version,
    render_page_about,
    render_page_help,
    render_page_test,
    renderer_assets,
    handle_rule_crud,
    handle_group_crud,
    handle_project_crud,
    handle_reorder,
    handle_app,
    handle_cmdlets,
    handle_functionality,
    handle_health,
    handle_qcrule_run,
)




# Each handler is registered together with the route it is mounted at (bound as
# `added_data`), so the handlers themselves stay agnostic of where they live —
# moving a handler to a different path only requires editing this one table.
endpoints = {
    '/': render_page_home,
    '/version': render_page_version,
    '/about': render_page_about,
    '/help': render_page_help,
    '/testpage': render_page_test,
    re.compile(r'^/qc/rules(?=$|/)'): partial(handle_rule_crud, added_data='/qc/rules'),
    re.compile(r'^/qc/groups(?=$|/)'): partial(handle_group_crud, added_data='/qc/groups'),
    re.compile(r'^/qc/reorder$'): partial(handle_reorder, added_data='/qc/reorder'),
    re.compile(r'^/qc/project(?=$|/)'): partial(handle_project_crud, added_data='/qc/project'),
    re.compile(r'^/app(?=$|/)'): partial(handle_app, added_data='/app'),
    re.compile(r'^/cmdlets(?=$|/)'): partial(handle_cmdlets, added_data='/cmdlets'),
    re.compile(r'^/functionality(?=$|/)'): partial(handle_functionality, added_data='/functionality'),
    '/health': partial(handle_health, added_data='/health'),
    re.compile(r'^/tests/run$'): partial(handle_qcrule_run, added_data='/tests/run'),

    re.compile('^/assets/.*'): renderer_assets,
}

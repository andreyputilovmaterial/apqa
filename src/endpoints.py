
import re

from .frontend.endpoints import (
    render_page_home,
    render_page_version,
    render_page_about,
    render_page_help,
    render_page_test,
    renderer_assets,
    handle_rule_crud,
    handle_definition_crud,
    handle_functionality,
    handle_rule_run,
)




endpoints = {
    '/': render_page_home,
    '/version': render_page_version,
    '/about': render_page_about,
    '/help': render_page_help,
    '/testpage': render_page_test,
    re.compile(r'^/qc/rules(?=$|/)'): handle_rule_crud,
    re.compile(r'^/qc/definitions(?=$|/)'): handle_definition_crud,
    re.compile(r'^/functionality(?=$|/)'): handle_functionality,
    re.compile(r'^/functionality/run-rule$'): handle_rule_run,

    re.compile('^/assets/.*'): renderer_assets,
}

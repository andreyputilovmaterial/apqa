
import re

from .frontend.endpoints import (
    render_page_home,
    render_page_version,
    render_page_about,
    render_page_help,
    render_page_test,
    renderer_assets,
)




endpoints = {
    '/': render_page_home,
    '/version': render_page_version,
    '/about': render_page_about,
    '/help': render_page_help,
    '/testpage': render_page_test,

    re.compile('^/assets/.*'): renderer_assets,
}

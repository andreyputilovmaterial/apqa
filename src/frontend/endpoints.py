
from .endpoints_html_paths import (
    render_page_home,
    render_page_version,
    render_page_about,
    render_page_help,
    render_page_test,
)
from .endpoints_assets_delivery_path import (
    renderer_assets,
)
from .endpoints_qcrules.rule_crud import (
    handle_rule_crud,
)
from .endpoints_qcrules.group_crud import (
    handle_group_crud,
)
from .endpoints_qcrules.project import (
    handle_project_crud,
)
from .endpoints_qcrules.reorder import (
    handle_reorder,
)
from .endpoints_app import (
    handle_app,
)
from .endpoints_cmdlets import (
    handle_cmdlets,
)
from .endpoints_functionality import (
    handle_functionality,
)
from .endpoints_health import (
    handle_health,
)
from .endpoints_qctests_run import (
    handle_qcrule_run,
)

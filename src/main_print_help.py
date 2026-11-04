

from rich.console import Console
from rich.markdown import Markdown


if __package__:
    from .GENERATED.HELP import _MD as help_md
else:
    # script context: `python src/main_print_help.py`. Add the repo root to
    # sys.path, then import through the `src` package.
    import os as _os, sys as _sys
    _sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
    from src.GENERATED.HELP import _MD as help_md


def print_help():
    console = Console()
    renderable_markup = Markdown(help_md)
    console.print(renderable_markup)
    print("\n\n\n")


if __name__ == '__main__':
    print_help()

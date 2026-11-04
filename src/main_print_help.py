

from rich.console import Console
from rich.markdown import Markdown


if __package__:
    from .GENERATED.HELP import _MD as help_md
else:
    # flat context: inlined with no parent package.
    from GENERATED.HELP import _MD as help_md


def print_help():
    console = Console()
    renderable_markup = Markdown(help_md)
    console.print(renderable_markup)
    print("\n\n\n")


if __name__ == '__main__':
    print_help()

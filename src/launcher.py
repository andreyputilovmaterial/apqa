
import argparse
# from pathlib import Path
import traceback, sys





# necessary adjustment for pinliner, as how I am using it.
#
# The SAME source file must work in several contexts, so imports are selected
# on `__package__` (which the import system sets reliably in every case):
#
#   * inside the `src` package  ->  relative imports (`from .GENERATED…`)
#     - `python -m src.launcher`            (`__package__ == 'src'`)
#     - `from src import launcher` in the pinliner bundle
#   * outside any package       ->  bootstrap the repo root onto sys.path and
#     import through `src` (absolute imports), so the package's relative imports
#     keep working further down
#     - `python src/launcher.py`            (script, repo root not yet on path)
#
# Only entry-point modules need this conditional import; every other module is
# only ever imported and uses plain relative imports.
if __package__:
    # package context: python -m src.launcher, or `from src import launcher`
    from .GENERATED.VERSION import _VERSION as gitgui_script_version
    from .GENERATED.HELP import _MD as help_md
    from .main_print_help import print_help
    from .main_ui_program import main as call_ui_program
    from .main_init_program import main as call_init_program
else:
    # script context: `python src/launcher.py`. The repo root is not on sys.path
    # yet, so add it, then import through the `src` package.
    import os as _os, sys as _sys
    _sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
    from src.GENERATED.VERSION import _VERSION as gitgui_script_version
    from src.GENERATED.HELP import _MD as help_md
    from src.main_print_help import print_help
    from src.main_ui_program import main as call_ui_program
    from src.main_init_program import main as call_init_program

gitgui_script_version = gitgui_script_version.strip()




# STDOUT_COLOR_RED = "\033[91m"
STDOUT_COLOR_RED = "\033[31m"
STDOUT_COLOR_RESET = "\033[0m"
STDOUT_COLOR_GREEN = "\033[32m"




def call_test_program(*argcs,**kwargs):
    msg = '''
hello, world! From gitgui
    '''
    print(msg)
    return True

def call_done_program(*argcs,**kwargs):
    msg = f'''
{STDOUT_COLOR_GREEN}done{STDOUT_COLOR_RESET}
    '''
    print(msg)
    return True

def call_printversion_program(*argcs,**kwargs):
    msg = gitgui_script_version
    msg = msg.strip()
    print(msg)
    return True

# def call_help_program(*argcs,**kwargs):
#     print_help()
#     return True




run_programs = {
    'ui': call_ui_program,
    'init': call_init_program,
    # 'project-selector': call_gitgui_project_selector_program,
    'test': call_test_program,
    'done': call_done_program,
    # 'help': call_help_program,
    'version': call_printversion_program,
}



def main():
    try:
        parser = argparse.ArgumentParser(
            description="Universal caller of mdmtoolsap-py utilities"
        )
        parser.add_argument(
            #'-1',
            '--program',
            choices=dict.keys(run_programs),
            type=str,
            required=True
        )
        args, args_rest = parser.parse_known_args()
        if args.program:
            program = f'{args.program}' # make sure it's text
            if program in run_programs:
                run_programs[program](args_rest)
            else:
                raise Exception('program to run not recognized: {program}'.format(program=args.program))
        else:
            # print(f'{STDOUT_COLOR_RED}program to run not specified{STDOUT_COLOR_RESET}')
            raise Exception('program to run not specified')
    except Exception as e:
        # the program is designed to be user-friendly
        # that's why we reformat error messages a little bit
        # stack trace is still printed (I even made it longer to 20 steps!)
        # but the error message itself is separated and printed as the last message again

        # for example, I don't write "print('File Not Found!');exit(1);", I just write "raise FileNotFoundErro()"
        print('',file=sys.stderr)
        print('Stack trace:',file=sys.stderr)
        print('',file=sys.stderr)
        traceback.print_exception(e,limit=20)
        print('',file=sys.stderr)
        print('',file=sys.stderr)
        print('',file=sys.stderr)
        print(f'{STDOUT_COLOR_RED}Error:{STDOUT_COLOR_RESET}',file=sys.stderr)
        print('',file=sys.stderr)
        print(f'{STDOUT_COLOR_RED}{e}{STDOUT_COLOR_RESET}',file=sys.stderr)
        print('',file=sys.stderr)
        exit(1)


if __name__ == '__main__':
    main()

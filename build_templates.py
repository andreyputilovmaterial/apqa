


import argparse
# from pathlib import Path
import traceback, sys
from datetime import datetime
from importlib import resources
from dataclasses import dataclass
from pathlib import Path
import re








from src.frontend.template.minify_assets import minify_js, minify_css
from src.frontend.bundler_engine.lib.py_js_bundler.src.run import process as pack_js



# STDOUT_COLOR_RED = "\033[91m"
STDOUT_COLOR_RED = "\033[31m"
STDOUT_COLOR_RESET = "\033[0m"
STDOUT_COLOR_GREEN = "\033[32m"


# def wrap_argparse_coloroutputs(Classname):
#     class Arg(Classname):
#


@dataclass
class Resource:
    filename: str
    payload: str
    is_binary: bool = False








def sanitize(input):
    return f'{input}'.replace(r'"""',r'\"""')


def scan_folder(path,is_binary=False):
    """Use this to generate the test_program_files_data """
    root = Path(path)
    excluded = {".git", "__pycache__",".DS_Store"}

    files_data = []


    for path in root.rglob("*"):
        def norm(path):
            return f'{path}'.replace('\\','/')
        if path.is_file():
            if any(part in excluded for part in path.parts):
                continue
            try:
                rel_path = path.relative_to(root)
                content = None
                try:
                    if not is_binary:
                        content = path.read_text(encoding="utf-8")
                    else:
                        with open(path,'rb') as f:
                            content = f.read()
                except Exception as e:
                    print(f'Failed reading {path}: {e}',file=sys.stdout)
                    content = None

                files_data.append((norm(str(rel_path)), content))
            except Exception as e:
                print(f'Failed processing {path}: {e}',file=sys.stdout)
                raise e

    return files_data




def build_normalize_css() -> list[Resource]:
    txt = resources.files("src.frontend.template.templates").joinpath("normalize.css").read_text('utf-8')
    txt = minify_css(txt)
    return [
            Resource(
            filename = "normalize.css",
            payload = txt
        ),
    ]

def build_common_css() -> list[Resource]:
    txt = resources.files("src.frontend.template.templates").joinpath("common.css").read_text('utf-8')
    txt = minify_css(txt)
    return [
        Resource(
            filename = "common.css",
            payload = txt
        ),
    ]

def build_projectspecific_css() -> list[Resource]:
    txt = ''
    txt += resources.files("src.frontend").joinpath("project_specific.css").read_text('utf-8')
    txt = minify_css(txt)
    return [
        Resource(
            filename = "project-specific.css",
            payload = txt
        ),
    ]

def build_common_js() -> list[Resource]:
    txt = ''
    txt += resources.files("src.frontend.template.templates").joinpath("common.js").read_text('utf-8')
    # txt += resources.files("src.frontend.template.templates").joinpath("app.js").read_text('utf-8')
    txt = minify_js(txt)
    return [
        Resource(
            filename = "common.js",
            payload = txt
        ),
    ]

def build_vendorlibs() -> list[Resource]:
    def build_resource_vue():
        txt_vue = ''
        # # uncomment for dev build
        # txt_vue += resources.files("src.frontend.assets_vendor_libs.vue").joinpath("vue.global.js").read_text('utf-8')
        # # # uncomment for prod build
        # # txt_vue += resources.files("src.frontend.assets_vendor_libs.vue").joinpath("vue.runtime.global.prod.js").read_text('utf-8')
        # # txt_vue = pack_js('./src/frontend/template/vendor/vue/vue.global.js')
        # # # txt_vue = pack_js('./src/frontend/template/vendor/vue/vue.runtime.global.prod.js')
        # uncomment for dev build
        txt_vue += resources.files("src.frontend.assets_vendor_libs.vue").joinpath("vue.esm-browser.js").read_text('utf-8')
        txt_vue = minify_js(txt_vue)
        return txt_vue
    def build_resource_marked():
        txt_marked = ''
        txt_marked += resources.files("src.frontend.assets_vendor_libs").joinpath("marked.umd.min.js").read_text('utf-8')
        txt_marked = minify_js(txt_marked)
        return txt_marked
    def build_resource_dompurify():
        txt_dompurify = ''
        txt_dompurify += resources.files("src.frontend.assets_vendor_libs").joinpath("purify.min.js").read_text('utf-8')
        txt_dompurify = minify_js(txt_dompurify)
        return txt_dompurify
    def build_resource_fonts_ibmplexsans():
        src = None
        dt = datetime.now()
        with resources.as_file(resources.files("src.frontend.assets_vendor_libs")) as f:
            src = Path(f) / 'fonts' / 'ibm-plex-sans'
            src = f'{src}'
            files = scan_folder(src,is_binary=True)
        result = []
        return [] \
            + [
                    Resource(filename=Path('vendorlibs/fonts/ibm-plex-sans') / file[0],payload=file[1],is_binary=True) \
                for file in files
            ] \
            + [
                Resource(filename="vendorlibs/fonts/ibm-plex-sans/_ASSETS_BUNDLED_PY.py",payload=f"\n\n# auto-generated: {dt}\n\n_ASSETS_VENDORLIBS_FONTS_IBMPLEXSANS = {repr(files)}\n")
            ]
    def build_resource_fonts_ibmplexmono():
        src = None
        dt = datetime.now()
        with resources.as_file(resources.files("src.frontend.assets_vendor_libs")) as f:
            src = Path(f) / 'fonts' / 'ibm-plex-mono'
            src = f'{src}'
            files = scan_folder(src,is_binary=True)
        result = []
        return [] \
            + [
                    Resource(filename=Path('vendorlibs/fonts/ibm-plex-mono') / file[0],payload=file[1],is_binary=True) \
                for file in files
            ] \
            + [
                Resource(filename="vendorlibs/fonts/ibm-plex-mono/_ASSETS_BUNDLED_PY.py",payload=f"\n\n# auto-generated: {dt}\n\n_ASSETS_VENDORLIBS_FONTS_IBMPLEXMONO = {repr(files)}\n")
            ]
    def build_resource_fonts_remixicon():
        src = None
        dt = datetime.now()
        with resources.as_file(resources.files("src.frontend.assets_vendor_libs")) as f:
            src = Path(f) / 'fonts' / 'remixicon'
            src = f'{src}'
            files = scan_folder(src,is_binary=True)
        result = []
        return [] \
            + [
                    Resource(filename=Path('vendorlibs/fonts/remixicon') / file[0],payload=file[1],is_binary=True) \
                for file in files
            ] \
            + [
                Resource(filename="vendorlibs/fonts/remixicon/_ASSETS_BUNDLED_PY.py",payload=f"\n\n# auto-generated: {dt}\n\n_ASSETS_VENDORLIBS_FONTS_REMIXICON = {repr(files)}\n")
            ]
    result = [
        Resource(
            filename = "vendorlibs/vue.js",
            payload = build_resource_vue()
        ),
        Resource(
            filename = "vendorlibs/marked.js",
            payload = build_resource_marked()
        ),
        Resource(
            filename = "vendorlibs/dompurify.js",
            payload = build_resource_dompurify()
        ),
    ]
    result += build_resource_fonts_ibmplexsans()
    result += build_resource_fonts_ibmplexmono()
    result += build_resource_fonts_remixicon()
    return result



def build_app_js() -> list[Resource]:
    # txt = ''
    # txt += resources.files("src.frontend.app_js").joinpath("app.js").read_text('utf-8')
    txt = pack_js('./src/frontend/app_js/src/app.js')
    txt = minify_js(txt)
    return [
        Resource(
            filename = "app.js",
            payload = txt
        ),
    ]

# def build_app_css() -> Resource:
#     txt = ''
#     txt += resources.files("src.frontend.app_js.src").joinpath("components.css").read_text('utf-8')
#     txt += resources.files("src.frontend.app_js.src").joinpath("app.css").read_text('utf-8')
#     txt = minify_css(txt)
#     return [
#         Resource(
#             filename = "app.css",
#             payload = txt
#         ),
#     ]




def build_py_dist() -> list[Resource]:
    raise Exception(f'Producing make_html.py: this should not be handled by build.py, call pinliner instead')
    # return [
    #     Resource(
    #         filename = "make_html.py",
    #         payload = sanitize(txt)
    #     ),
    # ]

def build_html_template() -> list[Resource]:
    # TEMPLATE_HTML_COPYBANNER = resources.files("src.frontend.template.templates").joinpath("copybanner.html").read_text('utf-8')
    TEMPLATE_HTML_TABLE_BEGIN = resources.files("src.frontend.template.templates").joinpath("table_begin.html").read_text('utf-8')
    TEMPLATE_HTML_TABLE_END = resources.files("src.frontend.template.templates").joinpath("table_end.html").read_text('utf-8')
    TEMPLATE_HTML_BEGIN = resources.files("src.frontend.template.templates").joinpath("html_begin.html").read_text('utf-8')
    TEMPLATE_HTML_END = resources.files("src.frontend.template.templates").joinpath("html_end.html").read_text('utf-8')
    f = ''
    f += '\n\n'
    f += 'TEMPLATE_HTML_BEGIN = r"""\n'+sanitize(TEMPLATE_HTML_BEGIN)+'\n"""\n\n'
    # f += 'TEMPLATE_HTML_END = r"""\n'+sanitize(TEMPLATE_HTML_END.replace(
    #         '{{TEMPLATE_HTML_COPYBANNER}}', TEMPLATE_HTML_COPYBANNER
    #     ))+'\n"""\n\n'
    f += 'TEMPLATE_HTML_END = r"""\n'+sanitize(TEMPLATE_HTML_END)+'\n"""\n\n'
    f += 'TEMPLATE_HTML_TABLE_BEGIN = r"""\n'+sanitize(TEMPLATE_HTML_TABLE_BEGIN)+'\n"""\n\n'
    f += 'TEMPLATE_HTML_TABLE_END = r"""\n'+sanitize(TEMPLATE_HTML_TABLE_END)+'\n"""\n\n'
    return [
        Resource(
            filename = "TEMPLATE.py",
            payload = f
        ),
        Resource(
            filename = "__init__.py",
            payload = ''
        ),
    ]

def build_blank() -> list[Resource]:
    return [
        Resource(
            filename = "__init__.py",
            payload = ''
        ),
    ]

renderers = {
    'blank': build_blank,
    'normalize.css': build_normalize_css,
    'common_css': build_common_css,
    'projectspecific_css': build_projectspecific_css,
    'common_js': build_common_js,
    'app_js': build_app_js,
    # 'app_css': build_app_css,
    'vendor-libs': build_vendorlibs,
    'make_html.py': build_py_dist,
    'src_template': build_html_template,
}





def call_build_program(*argcs,**kwargs):
    time_start = datetime.now()
    script_name = 'html-template build'

    parser = argparse.ArgumentParser(
        description="Produce html template",
        prog='htmltemplate --program build'
    )
    parser.add_argument(
        '--resource',
        help='resource',
        type=str,
        choices = dict.keys(renderers),
        required=True
    )
    parser.add_argument(
        '--dest',
        help='Set dest location',
        type=str,
        required=False
    )
    # args = None
    # args_rest = None
    # if( ('arglist_strict' in config) and (not config['arglist_strict']) ):
    #     args, args_rest = parser.parse_known_args()
    # else:
    args = None
    try:
        args = parser.parse_args(*argcs,**kwargs)
    except SystemExit as e:
        print(f'{STDOUT_COLOR_RED}Error: Invalid command-line arguments{STDOUT_COLOR_RESET}',file=sys.stderr)
        raise e

    res_processed = None
    if args.resource:
        res_processed = f'{args.resource}'

    out_path = None
    if args.dest:
        out_path = Path(args.dest).resolve()

    print(f'{script_name}: script started at {time_start}')

    renderer = renderers.get(res_processed,None)
    results = None
    if not renderer:
        raise Exception(f'Can\'t build given resource and find handler: {res_processed}')
    try:
        print(f'{script_name}: building {res_processed}...')
        results = renderer()
    except Exception as e:
        print(f'{STDOUT_COLOR_RED}Failed when building {res_processed}: {e}{STDOUT_COLOR_RESET}',file=sys.stderr)
        raise e

    for result in results:
        result_fname = Path(out_path) / result.filename
        try:
            print('{script_name}: saving as "{fname}"'.format(fname=result_fname,script_name=script_name))
            result_fname.parent.mkdir(parents=True, exist_ok=True)
            with open(result_fname, 'wb' if result.is_binary else 'w', encoding=None if result.is_binary else 'utf-8') as outfile:
                outfile.write(result.payload)
        except Exception as e:
            print(f'{STDOUT_COLOR_RED}processing resource failed!{STDOUT_COLOR_RESET}',file=sys.stdout)
            print(f'{STDOUT_COLOR_RED}file: {result.filename}{STDOUT_COLOR_RESET}',file=sys.stdout)
            print(f'{STDOUT_COLOR_RED}path: {result_fname}{STDOUT_COLOR_RESET}',file=sys.stdout)
            print(f'{STDOUT_COLOR_RED}is_binary: {result.is_binary}{STDOUT_COLOR_RESET}',file=sys.stdout)
            print(f'repr: {repr(result.payload)}',file=sys.stdout)
            raise e

    time_finish = datetime.now()
    print(f'{script_name}: {STDOUT_COLOR_GREEN}finished at {time_finish} (elapsed {time_finish-time_start}){STDOUT_COLOR_RESET}')



def call_bundle_program(*argcs,**kwargs):
    time_start = datetime.now()
    script_name = 'build helper'

    parser = argparse.ArgumentParser(
        description="Produce py",
        prog='htmltemplate --program bundle-file-into-py'
    )
    parser.add_argument(
        '--varname',
        help='varname',
        type=str,
        required=True
    )
    # args = None
    # args_rest = None
    # if( ('arglist_strict' in config) and (not config['arglist_strict']) ):
    #     args, args_rest = parser.parse_known_args()
    # else:
    args = None
    try:
        args = parser.parse_args(*argcs,**kwargs)
    except SystemExit as e:
        print(f'{STDOUT_COLOR_RED}Error: Invalid command-line arguments{STDOUT_COLOR_RESET}',file=sys.stderr)
        raise e

    txt = sys.stdin.buffer.read().decode(encoding='utf-8')

    # print(f'{script_name}: script started at {time_start}')

    result = f'''
# THIS IS AUTO_GENERATED
# updated {time_start}

{args.varname} = {repr(txt)}

'''

    sys.stdout.buffer.write(result.encode(encoding='utf-8'))

    time_finish = datetime.now()
    # print(f'{script_name}: {STDOUT_COLOR_GREEN}finished at {time_finish} (elapsed {time_finish-time_start}){STDOUT_COLOR_RESET}')



def _parse_requirements(text):
    """Return the installable requirement specifiers in a requirements.txt body.

    Mirrors the subset of pip's parser that cmdlet requirements.txt files use:
    blank lines and whole-line comments (leading ``#``) are skipped, a trailing
    comment (a ``#`` preceded by whitespace) is stripped, and everything else is
    kept verbatim as a single specifier. A ``#`` that is not preceded by
    whitespace (e.g. a VCS ``#egg=`` fragment) is kept.
    """
    result = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        stripped = re.sub(r'\s+#.*$', '', stripped).strip()
        if stripped:
            result.append(stripped)
    return result


def collect_optional_dependencies():
    """Scan ``src/cmdlets/**/requirements.txt`` and return ``[(name, specs), ...]``.

    ``name`` is the cmdlet folder name and ``specs`` the list of installable
    requirement specifiers. Comment-only files (stdlib-only cmdlets) are dropped:
    there is nothing to install for them. The scan runs on the real source tree,
    so it works both during ``build.sh`` and from a test run.
    """
    root = Path(__file__).resolve().parent / 'src' / 'cmdlets'
    result = []
    if not root.is_dir():
        return result
    for requirements_file in sorted(root.glob('*/requirements.txt')):
        specs = _parse_requirements(requirements_file.read_text(encoding='utf-8'))
        if specs:
            result.append((requirements_file.parent.name, specs))
    return result


def _sh_quote(spec):
    return "'" + spec.replace("'", "'\\''") + "'"


def _bat_quote(spec):
    # `%` is special in batch files; `%%` is its escaped form. Keep every other
    # character as-is — inside double quotes &, |, <, > are literal.
    return '"' + spec.replace('%', '%%') + '"'


def _render_sh_optional_deps(entries):
    lines = [
        '# Optional per-cmdlet dependencies (inlined by build.sh from',
        '# src/cmdlets/**/requirements.txt). Each install is best-effort: a missing',
        '# optional dependency must not fail the whole init — the affected cmdlet is',
        '# imported as "unavailable" and raises its import error only when used.',
    ]
    for name, specs in entries:
        quoted = ' '.join(_sh_quote(spec) for spec in specs)
        lines.append('echo "Installing optional dependencies: {0}"'.format(name))
        lines.append('if ! "$pythonexecutable" -m pip install {0}; then'.format(quoted))
        lines.append(
            '    echo "WARNING: optional dependencies for {0} not installed'
            ' (the corresponding cmdlets will be unavailable)"'.format(name)
        )
        lines.append('fi')
        lines.append('')
    return '\n'.join(lines) + '\n'


def _render_bat_optional_deps(entries):
    lines = [
        '@REM Optional per-cmdlet dependencies (inlined by build.sh from',
        '@REM src\\cmdlets\\**\\requirements.txt). Each install is best-effort: a missing',
        '@REM optional dependency must not fail the whole init — the affected cmdlet is',
        '@REM imported as "unavailable" and raises its import error only when used.',
    ]
    for name, specs in entries:
        quoted = ' '.join(_bat_quote(spec) for spec in specs)
        lines.append('echo Installing optional dependencies: {0}'.format(name))
        lines.append('"%pythonexecutable%" -m pip install {0}'.format(quoted))
        lines.append(
            'if errorlevel 1 echo WARNING: optional dependencies for {0} not installed'
            ' - the corresponding cmdlets will be unavailable'.format(name)
        )
        lines.append('')
    return '\n'.join(lines) + '\n'


def _replace_between_markers(text, begin_marker, end_marker, replacement):
    lines = text.splitlines(keepends=True)
    begin = None
    end = None
    for index, line in enumerate(lines):
        if begin_marker in line and begin is None:
            begin = index
        elif end_marker in line and begin is not None:
            end = index
            break
    if begin is None or end is None or end < begin:
        return text
    return ''.join(lines[:begin] + [replacement] + lines[end + 1:])


def call_transform_run_script_program(*argcs, **kwargs):
    time_start = datetime.now()
    script_name = 'transform run script'

    parser = argparse.ArgumentParser(
        description="Adapt a root-level run_*.sh/.bat script for the dist/ layout",
        prog='build_templates --program transform-run-script'
    )
    parser.add_argument(
        '--input',
        help='Source run script (root-level)',
        type=str,
        required=True
    )
    parser.add_argument(
        '--output',
        help='Destination run script (dist/)',
        type=str,
        required=True
    )
    args = None
    try:
        args = parser.parse_args(*argcs, **kwargs)
    except SystemExit as e:
        print(f'{STDOUT_COLOR_RED}Error: Invalid command-line arguments{STDOUT_COLOR_RESET}', file=sys.stderr)
        raise e

    src_text = Path(args.input).read_text(encoding='utf-8')
    # .bat scripts use backslash path separators, .sh scripts use forward slashes.
    sep = chr(92) if args.input.endswith('.bat') else '/'

    # 1. strip the dev-only "build the bundle first" block (inclusive of its markers)
    lines = src_text.splitlines(keepends=True)
    kept = []
    inside_block = False
    for line in lines:
        if 'BEGIN BUILD-ONLY' in line:
            inside_block = True
            continue
        if 'END BUILD-ONLY' in line:
            inside_block = False
            continue
        if not inside_block:
            kept.append(line)
    result = ''.join(kept)

    # 2. point at the bundle instead of the dev launcher / dev pytest target
    result = result.replace('-m src.launcher', 'apqa_bundle.py')
    result = result.replace(f'dist{sep}apqa_bundle.py', 'apqa_bundle.py')

    # 3. the data directory lives one level up from dist/
    result = result.replace(
        f'tests-real-sensitive-data{sep}',
        f'..{sep}tests-real-sensitive-data{sep}'
    )

    # 4. inline optional per-cmdlet dependencies (dist/ keeps no per-cmdlet
    #    requirements.txt files — the pip install statements are embedded here)
    if 'BEGIN OPTIONAL-DEPS' in result:
        entries = collect_optional_dependencies()
        if args.input.endswith('.bat'):
            replacement = _render_bat_optional_deps(entries)
        else:
            replacement = _render_sh_optional_deps(entries)
        result = _replace_between_markers(
            result, 'BEGIN OPTIONAL-DEPS', 'END OPTIONAL-DEPS', replacement
        )

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(result, encoding='utf-8')

    time_finish = datetime.now()
    print(f'{script_name}: {STDOUT_COLOR_GREEN}finished at {time_finish} (elapsed {time_finish-time_start}){STDOUT_COLOR_RESET}')


run_programs = {
    'build': call_build_program,
    'bundle-file-into-py': call_bundle_program,
    'transform-run-script': call_transform_run_script_program,
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
        args = None
        args_rest = None
        try:
            args, args_rest = parser.parse_known_args()
        except SystemExit as e:
            print(f'{STDOUT_COLOR_RED}Error: Invalid command-line arguments{STDOUT_COLOR_RESET}',file=sys.stderr)
            raise e
        if args.program:
            program = f'{args.program}'
            if program in run_programs:
                run_programs[program](args_rest)
            else:
                raise AttributeError(f'program to run not recognized: {args.program}')
        else:
            print('program to run not specified')
            raise AttributeError('program to run not specified')
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
        print('Error:',file=sys.stderr)
        print('',file=sys.stderr)
        print(f'{STDOUT_COLOR_RED}{e}{STDOUT_COLOR_RESET}',file=sys.stderr)
        print('',file=sys.stderr)
        exit(1)


if __name__ == '__main__':
    main()

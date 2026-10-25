# APQA — developer & architecture guide

This document describes *how* APQA is built and the constraints that shape the
code. It is intended for contributors and maintainers, not for end users. For the
user-facing picture, see the [README](../README.md) and the in-app Help page
([`help.md`](../help.md)).

> Some of the rationale below originally lived in the author's design notes, now
> archived at [`design-notes.md`](design-notes.md).

## What APQA is

APQA is a Python tool for defining, managing, and running **QC (quality-control)
rules** for a research project. It has two run modes:

1. **Desktop app (edit rules)** — a Python backend + Vue frontend served from
   `localhost` (`--program ui --db-file <path>`).
2. **Run the QC rules** — the program is invoked through `pytest`, which runs every
   rule against the source data and reports pass/fail.

The project is selected by pointing the program at a **rules database file**
(SQLite by default; YAML also supported): `--db-file` in the desktop app, or the
`APQA_DB_FILE` environment variable in the run-tests mode (CLI args are not
available there). The format is chosen by the file extension.

## Distribution model: the pinliner bundle

The distributable is a single self-contained Python file, `dist/apqa_bundle.py`,
produced by `build.sh` using [pinliner]
(`src_dev_build/lib/pinliner`, a git submodule). Everything in the codebase is
shaped so that this bundle keeps working:

- **Relative imports only.** `.py` files use only relative imports. The single
  exception is `src/launcher.py`, which conditionally imports depending on how it
  is invoked (as `__main__`, as a package, or inlined with no parent package).
- **No top-level imports.** If genuinely needed, `src/launcher.py` loads the entry
  module, that module imports what it needs and stores it on a global config
  object, which is then passed down. This is discouraged — avoid it.
- **`__init__.py` at every level.** pinliner requires `__init__.py` on every
  imported-module path even though modern Python does not. When adding a package
  or submodule, add its `__init__.py`.

### No runtime files

The app must not depend on separate local files at runtime: no `.env`, no
standalone JS/CSS assets, no `help.md`/`version.md`. Anything needed at runtime is
embedded in the bundle or importable as a Python module — via the `GENERATED/`
folders that `build.sh` produces.

This does **not** forbid reading *user-provided* files at runtime (a QC rule reads
source data from a full filesystem path).

## Building

`build.sh` is the single build entry point and must work after a fresh clone:

- It runs `git submodule update --init --recursive`.
- It generates `src/GENERATED/` (version, embedded help) and
  `src/frontend/GENERATED/` (bundled/minified assets) so the program can run even
  in development.
- It runs pinliner to produce `dist/apqa_bundle.py`, then **patches** the bundle by
  appending the pytest entry point at the end.

Only append to the bundle — pinliner hard-codes where each module starts and ends,
so patching anywhere else would corrupt it. Appending at the very end is safe
because it is beyond all recorded positions.

### Run scripts (root → dist)

The `run_*.sh` / `run_*.bat` scripts in the repo root are the source of truth and run
from the root during development. They launch the program as `python -m src.launcher`
(note: `python src/launcher.py` does **not** work — its `__main__` branch imports
`src.GENERATED.*`, which needs the repo root on `sys.path`) and point at
`tests-real-sensitive-data/`.

`build.sh` copies them into `dist/` while adapting them for the distributed layout
(via `build_templates.py --program transform-run-script`):

- `-m src.launcher` → `apqa_bundle.py`
- `dist/apqa_bundle.py` → `apqa_bundle.py` (the `run_tests` pytest target)
- `tests-real-sensitive-data/` → `../tests-real-sensitive-data/` (the data directory
  lives one level above `dist/`)
- the dev-only "build the bundle first" block in `run_tests.*` is stripped

`run_tests.*` run QC rules through pytest, whose entry point exists only inside the
bundle. So from the root they first run `build.sh` and then pytest on
`dist/apqa_bundle.py`; the distributed copy skips the build and runs `apqa_bundle.py`
directly.

## Optional dependencies

The global [`requirements.txt`](../requirements.txt) lists only the packages the
whole app needs. Individual cmdlets (and, later, processors) may need extra
packages that are **not required app-wide** — e.g. `openpyxl` to read Excel,
`pyreadstat` to read SPSS, `pandas` for some data formats, `pywin32` for the
Windows COM API — and that may be **platform-specific** (`pywin32` only exists on
Windows).

These are *optional dependencies*. A missing one must never break the app: you
must be able to add, edit, and delete a rule that references an Excel-reading
cmdlet on a machine without `openpyxl` installed. Only *running* that cmdlet
raises its import error.

### Specifying them (encapsulation)

Each cmdlet that needs optional dependencies lives in its own folder under
`src/cmdlets/`, with the `requirements.txt` kept next to it (not in a global
list), so the cmdlet stays self-contained and liftable:

    src/cmdlets/get_content_excel/
        __init__.py        # guards the optional import, then registers the cmdlet
        requirements.txt   # e.g. "openpyxl>=3"

### Import time: capture, don't fail

Each cmdlet guards its own optional import at module level and stores the
captured error, so the module always loads and the cmdlet is always registered
(and can be listed/referenced). The error is only raised at the start of the
cmdlet's runtime function:

    try:
        import openpyxl
    except Exception as error:          # no exception-type branching
        openpyxl = None
        _import_error = error
    else:
        _import_error = None

    @cmdlets.register('get-content-excel')
    def get_content_excel(value, args):
        if _import_error is not None:
            raise ImportError(
                "get-content-excel: missing optional dependency 'openpyxl'"
            ) from _import_error
        ...

So rules can be added/edited/deleted that reference the cmdlet without the
dependency installed; only *running* the cmdlet raises a readable
missing-dependency error. Each cmdlet is responsible for its own optional
import — there is no global import-error machinery.

### Build & install

`build.sh` auto-discovers every `src/cmdlets/**/requirements.txt` (a plain
filesystem search on the real source tree — this runs before/outside the bundle,
so pinliner is not involved) and copies it into
`dist/optional_dependencies/<path-under-src>/requirements.txt`. `run_init.sh` and
`run_init.bat` install each one best-effort (a failure prints a WARNING and
continues). `build_templates.py --program transform-run-script` rewrites the
`src/cmdlets` path to `optional_dependencies` in the distributed copies of the
run scripts.

### Adding a new optional cmdlet

1. Create `src/cmdlets/<module_name>/` with `__init__.py` (guard the optional
   import, store the error, register the cmdlet, and raise a readable error at
   the start of its runtime function) and `requirements.txt`.
2. Import the module from `src/cmdlets/__init__.py`
   (`from . import <module_name>`), like `count`.
3. Done — `build.sh` and `run_init.*` pick the `requirements.txt` up
   automatically.

## Frontend & build

- The web server is **self-written** (`src/webserver_engine/webserve`, a submodule),
  a wrapper around Python's `http.server` — **no Flask/Django**. It handles all
  HTTP methods (POST, PUT, DELETE, …), even if it looks GET-only at first glance.
- Frontend apps may use **only `.js` and `.css`** — **no `.vue` and no `.ts`**
  (a limitation of the self-written JS bundler
  `src/frontend/bundler_engine/lib/py_js_bundler`, a submodule). The bundler is raw
  and being extended; it may be replaced later.
- The UI is Vue, but written as plain `.js` + `.css` (Vue is served as a vendored JS
  asset), so it still satisfies the no-`.vue`/no-`.ts` rule.
- The build must be possible **without Node installed**. Node/vite may be used only
  to speed up frontend development.
- Prefer **relative imports** so components stay self-contained and liftable. The
  `@` alias points at the app root (`src/frontend/app_js/src`, defined in
  `jsconfig.json` → `compilerOptions.paths`) and is resolved by both Vite and the
  self-written bundler; use `@/...` rather than deep `../../..` when a component must
  reach up to an outer level.
- `src/frontend/template/templates/common.css` is the shared global "skin" loaded
  by every page. It is broad by design, so do **not** use it for per-component
  layout fixes — those belong in the component's own `.css`. Any change to
  `common.css` must be logged (with date + reason) in
  `src/frontend/template/templates/common.css.changelog.md` (see
  `.clinerules/09-frontend-common-css.md`).
- Name UI modules after what they show: the QC-rule list lives in
  `src/frontend/app_js/src/app/qcrules_list/` (component `QcRulesList`, CSS
  classes `apqa-qcrules-list*`). Reserve the word "project" for an actual
  project list, not for the QC-rule list.

## Testing

There are two distinct uses of pytest — do not conflate them:

1. **Development tests** (verify program functionality). These live in `tests/`
   and are **not** included in the final bundle.
2. **“Run QC tests” mode** (the product feature). The final bundle contains a
   **single discoverable parametrized entry point** (appended by `build.sh`) that
   reads rules from the DB file. There is **no physical test discovery** — one entry
   point parametrized from the database.

Notes:

- The QC-rules DB file is passed via `APQA_DB_FILE` (set by the caller `.sh`/`.bat`
  script). User CLI params are not available in this mode.
- `--import-mode=importlib` is required **only** when running the bundle under
  pytest (a pinliner limitation). It is unnecessary for development tests.
- The QC rules stored in the project DB (SQLite or YAML) are the fixtures and
  acceptance criteria.
- `tests-real-sensitive-data/` is gitignored (sensitive/proprietary data). Never
  commit it.

### Why pytest, and is it permanent?

The **function** we need is simple: run each rule, then exit zero/non-zero and say
which rules failed. That could be done without pytest.

pytest is used today because it is the standard, widely supported test environment
(and effectively the only one this project's author knows well): it gives pass/fail
marks, an HTML report plugin (`pytest-html`), and a large ecosystem of tools.

Two acknowledged downsides:

1. **It may be an unnecessary dependency** — pytest brings machinery we don't
   strictly need for a zero/non-zero exit status.
2. **It muddies the word “tests”** — “running QC rules” is *running the program*,
   not *testing the program*, which is easy to confuse with development tests.

Why the confusion is contained in practice:

- The bundle is distributed **without** `tests/`, so development tests can't be
  mistaken for the run-QC-rules mode.
- The run-QC-rules entry point is **appended by `build.sh`** and therefore exists
  only in the final bundle, never in the source tree.

So pytest is a pragmatic *starting point*, not a hardcoded decision. It can be
replaced or migrated away if a concrete reason appears.

## QC rule domain model

> The authoritative specification for cmdlet value formats, comparison
> semantics, and cmdlet naming is
> [`cmdlet-data-formats.md`](cmdlet-data-formats.md); this section summarizes
> the domain model that the runner and storage follow.

A QC rule has three essential parts: **left side**, **comparison op**, **right side**.

- Left and right sides are **chains of cmdlets** (PowerShell-like pipes), e.g.:
  `get-content Specs.xlsx | select-item "Title Details" | select-property "B" | count`.
- Stored shape of a cmdlet: `{ cmdlet: <name>, args: { <param>: <value>, ... } }`.
  `args` is always a named mapping (flags like `-Recurse` become `{ recurse: true }`)
  and may be omitted when empty. `args` values are **not restricted to strings**:
  they are JSON-serializable, so a value may be a number, a boolean, a list, an
  object, or even a nested cmdlet / chain of cmdlets (see `map` below).
- Stored shape of a rule: `name` (unique), `meta` (extensible: `created_by`,
  `created_at`, `modified_at`, `comment`, `tags`, `markers`, …),
  `left` (list of cmdlets), `op` (string), `op_args` (optional mapping,
  JSON-serializable), `right` (list of cmdlets).
- `op` is a registered comparison op name (e.g. `eq`, `ne`, `eq-unordered`,
  `lt`, `gt`, `contains`). `eq`/`ne` compare compound values deeply (blocks by
  field name, order-insensitive; arrays in strict position order); the ordering
  ops (`lt`/`le`/`gt`/`ge`) are scalar-only. `op_args` (optional) passes
  op-specific options, e.g. `eq`/`ne` accept
  `op_args: { unordered_arrays: true }` for order-agnostic array comparison;
  `eq-unordered` is that flag hard-wired.

Three cmdlet types:

1. **Source readers** — read source data (Excel, SPSS, CSV, text, databases, …).
2. **Middle processors** — `select-property`, `select-properties`,
   `select-item`, `where`, `map`, `sort`, `count`, `to-string`, …
3. **Terminal** — produce a value for comparison.

Cmdlets are defined through a **global registry** (plugin-like) and are
extensible — especially type-1 source readers. Prefer a minimal but flexible set of
middle/terminal cmdlets and avoid source-specific cmdlets (no dedicated
“read-excel-sheet”): one generic operation should work across Excel/SPSS/DB/etc.

Scalar types a cmdlet can return: text, int, float, bool, path, date/time,
single-punch categorical, multi-punch categorical. Compound types: **block**
(named fields), **named collection** (provisional — see
`cmdlet-data-formats.md`), and **array** (a block repeated per iteration).

**`map` (ForEach-Object).** `map` transforms each iteration of an array. Its
argument is a **chain of cmdlets** (or a single cmdlet) run once per iteration,
with the iteration threaded through as the piped value. A chain is a list of
`{ cmdlet, args }` mappings, so it is JSON-serializable and stores in the DB
without special handling. Proposed shape:

    { "cmdlet": "map", "args": { "transform": [ { "cmdlet": "...", "args": {} }, … ] } }

`args["transform"]` may also be a single cmdlet mapping (not wrapped in a list).

**`sort`.** `sort` reorders an array: `args.by` (optional) sorts blocks by a
field, without it an array of scalars sorts naturally, and
`args.descending: true` reverses the result. See `cmdlet-data-formats.md`.

**`sysmissing`:** every value may be `sysmissing`, regardless of type. In comparison,
`sysmissing` is undefined/uncertain — it equals only another `sysmissing`. Comparing
`sysmissing` to an empty set/collection, zero, `false`, or empty string returns
`false`.

The same design principles apply to the DB storage format, the UI, and what flows
through the pipe. Rules may carry pytest modifiers in `meta.markers`: `skip`
(do not run) and `xfail` (a failure is expected and treated as normal).

**Planned (not implemented): conditional markers.** Some rules rely on cmdlets
whose tools exist only on some platforms (e.g. `pywin32` on Windows). The idea is
a marker that skips a rule unless a condition holds, driven by environment
variables set by the outer `run_*.sh`/`.bat` script (which can compute a value
such as `APQA_PLATFORM=windows`). Real expressions can't run inside markers, so
complex logic stays in the outer script and exposes its result as an env var;
the marker then just checks that variable. Placeholder only.

### Rules database storage

The rules database is a format-agnostic interface
(`src/db_processors/dbfile_base.py`) with backends selected by file extension via
`detect_type`:

- **SQLite** (`.sqlite3`/`.sqlite`) — the default. Each rule is one row; `meta`,
  `left` and `right` are stored as JSON text, `name`/`op`/`group` as plain text.
  Two parallel tables store project-level aliases (`definitions`: `name`,
  `value`, `meta`) and rule groups/folders (`groups`: `name`, `parent`, `meta`).
- **YAML** (`.yaml`/`.yml`) — a mapping with three optional lists, `definitions`,
  `groups` and `rules`. A legacy top-level list of rules is still accepted (read
  as rules only).

Both backends implement the same CRUD contract for rules (`list_rules`,
`get_rule`, `has_rule`, `add_rule`, `update_rule`, `rename_rule`,
`delete_rule`, `save`), the matching definition contract (`list_definitions`,
`get_definition`, `has_definition`, `add_definition`, `update_definition`,
`rename_definition`, `delete_definition`), and a group contract
(`list_groups`, `get_group`, `has_group`, `add_group`, `update_group`,
`rename_group`, `delete_group`). Rules return `Rule` objects; definitions return
`Definition` objects (`name`, `value`, `meta`); groups return `Group` objects
(`name`, `parent`, `meta`). Groups form a tree via `parent` (`''` = top level)
and rules reference their folder via `Rule.group`; renaming a group cascades to
its rules and child groups, and deleting a non-empty group is refused. The
SQLite backend is thread-safe (the web server is a `ThreadingHTTPServer`) via a
re-entrant lock around a single shared connection.

## Code style & error handling

- **Fail early** with a **readable error message** — detect wrong/missing things
  upfront rather than failing later with a cryptic missing-attribute error.
- **Do not over-validate** — leave flexibility for data format; stay Pythonic.

## Submodules

Reusable code is deliberately extracted into git submodules (an established habit
in this repo). Prefer submodules for separable pieces. Current submodules:
`pinliner`, `webserve`, `py_js_bundler`.
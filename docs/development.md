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
   enabled rule against the source data and reports pass/fail.

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

A QC rule has three essential parts: **left side**, **comparison op**, **right side**.

- Left and right sides are **chains of cmdlets** (PowerShell-like pipes), e.g.:
  `get-content Specs.xlsx | select-sheet "Title Details" | select-column "B" | count`.
- Stored shape of a cmdlet: `{ cmdlet: <name>, args: { <param>: <value>, ... } }`.
  `args` is always a named mapping (flags like `-Recurse` become `{ recurse: true }`)
  and may be omitted when empty.
- Stored shape of a rule: `name` (unique), `meta` (extensible: `enabled`,
  `created_by`, `created_at`, `modified_at`, `comment`, `tags`, `markers`, …),
  `left` (list of cmdlets), `op` (string), `right` (list of cmdlets).
- `op` is a registered comparison op name, always scalar vs scalar
  (e.g. `eq`, `lt`, `gt`, `contains`).

Three cmdlet types:

1. **Source readers** — read source data (Excel, SPSS, CSV, text, databases, …).
2. **Middle processors** — `select-column`, `map`, `count`, `to-string`, …
3. **Terminal** — produce a scalar for comparison.

Cmdlets are defined through a **global registry** (plugin-like) and are
extensible — especially type-1 source readers. Prefer a minimal but flexible set of
middle/terminal cmdlets and avoid source-specific cmdlets (no dedicated
“read-excel-sheet”): one generic operation should work across Excel/SPSS/DB/etc.

Scalar types a cmdlet can return: text, int, float, bool, date/time, single-punch
categorical, multi-punch categorical. Compound types (object with named fields,
collection of uniform objects, tuple) are still being finalized.

**`sysmissing`:** every value may be `sysmissing`, regardless of type. In comparison,
`sysmissing` is undefined/uncertain — it equals only another `sysmissing`. Comparing
`sysmissing` to an empty set/collection, zero, `false`, or empty string returns
`false`.

The same design principles apply to the DB storage format, the UI, and what flows
through the pipe. Rules may carry pytest modifiers (e.g. `xfail`) in `meta.markers`.

### Rules database storage

The rules database is a format-agnostic interface
(`src/db_processors/dbfile_base.py`) with backends selected by file extension via
`detect_type`:

- **SQLite** (`.sqlite3`/`.sqlite`) — the default. Each rule is one row; `meta`,
  `left` and `right` are stored as JSON text, `name`/`op` as plain text.
- **YAML** (`.yaml`/`.yml`) — a list of rule mappings.

Both backends implement the same CRUD contract (`list_rules`, `get_rule`,
`has_rule`, `add_rule`, `update_rule`, `rename_rule`, `delete_rule`, `save`) and
return `Rule` objects. The SQLite backend is thread-safe (the web server is a
`ThreadingHTTPServer`) via a re-entrant lock around a single shared connection.

## Code style & error handling

- **Fail early** with a **readable error message** — detect wrong/missing things
  upfront rather than failing later with a cryptic missing-attribute error.
- **Do not over-validate** — leave flexibility for data format; stay Pythonic.

## Submodules

Reusable code is deliberately extracted into git submodules (an established habit
in this repo). Prefer submodules for separable pieces. Current submodules:
`pinliner`, `webserve`, `py_js_bundler`.
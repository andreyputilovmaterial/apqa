# Project context

> Living document. Updated after every task. Read this first at the start of every task.

## Last state

- Implemented the **UI "projects list"** in `src/frontend/app_js`: the list of QC
  rules (the home page is literally "Manage QC rule list"; here "projects" == the
  QC-rule records). `app/projects_list/index.js` fetches `GET /qcrules`, flattens
  each rule into a filterable record (`name`, `op`, `enabled`, `comment`, `tags`,
  `created_at`, `modified_at`, plus formatted `left`/`right` cmdlet chains) and
  renders them.
- Ported the **RecordsFilter** component from apphotoassistant
  (`frontend/src/components/records-filter/RecordsFilter.vue`) into
  `common_components/records_filter/` as plain `.js` + `.css` (no `.vue`):
  `index.js` (Vue component), `matchers.js` (pure match/sort), `matchers.spec.js`
  (22 vitest tests, all passing), `styles.css`, `README.md`. It keeps the
  **two-level filtering** (css-class `.apqa-u-hidden` for recently-hidden records +
  physical removal after a 5-min TTL) so records aren't destroyed while the user is
  typing. The projects list is wrapped in it.
- Added an **error banner** (`app/apppane_errorview/`) plus an error-reporting
  composable (`common_app_exposed_defs/error_reporting/index.js`) that wires the
  existing `common_components/_log_error_proxy` (resolves `promiseResolve`).
- Wired everything in `app.js` (root template now renders the error banner, the
  projects list, `background-navlinks-attachmodals` and `modals-site`; sets up
  `useErrorReporting` and exposes `repoActions = { logError, createModal }`). Added
  a `/qcrules` proxy entry to `vite.config.js` for dev mode.
- Validated: `matchers.spec.js` (22 tests) passes; the self-written `py_js_bundler`
  bundles `app.js` (110 KB); `vite build` transforms 57 modules with no errors.

## Recent history (previous task)

- Added a **SQLite rules database backend** (`src/db_processors/sqlite.py`, type
  `'sqlite'`), the documented default alongside YAML, selected purely by file
  extension via `detect_type`. One row per rule (`name` PK; `meta`/`"left"`/`"right"`
  as JSON text; `op` as text). Thread-safe via `threading.RLock` +
  `check_same_thread=False`; write-through; requires the file to exist (schema
  auto-created on first open). SQLite serializes date/time to ISO-8601 strings via
  `_RuleEncoder` (YAML round-trips `datetime`; documented asymmetry).
- Also moved the generic `.rules` accessor up to `DBFile` (base) and removed the
  YAML-only duplicate; 398 dev tests passed.

## Repo overview

- **APQA** — a quality-control (QC) rules engine: define/manage rules, then run them
  as tests.
- Two run modes: (1) desktop app (`--program ui --db-file <path>`) to edit rules,
  (2) run QC rules via `pytest`
  (`APQA_DB_FILE=<path> … -m pytest --import-mode=importlib apqa_bundle.py`).
- Bundled with `pinliner` into a single self-contained `dist/apqa_bundle.py` via
  `build.sh`.
- UI is Vue but written as plain `.js`/`.css` (no `.vue`/`.ts`).
- QC rules live in a DB (SQLite by default; YAML also supported) and are the
  fixtures/acceptance criteria. Storage backends register in
  `src/db_processors/dbfile_base.py` and are selected by extension in
  `detect_type.py`.

## Key conventions / gotchas

- Only **relative imports** in `.py`; imported-module paths need `__init__.py` at
  each level (`src/launcher.py` is the only import exception).
- No runtime dependency on separate local files (no `.env`, no standalone JS/CSS);
  runtime content is embedded via `GENERATED/` folders.
- `--import-mode=importlib` only when running the bundle under pytest (not dev tests).
- `tests-real-sensitive-data/` is gitignored — never commit it.
- pytest for "run QC rules" is a pragmatic starting point, not a hardcoded decision
  (see `.clinerules/03-testing.md` and `docs/development.md`).
- New storage backends must implement the full CRUD contract in
  `dbfile_base.py` **and** be imported in `db_processors/__init__.py` (import = the
  `@DBFile.register(...)` side effect). Generic accessors like `.rules` belong on
  the base class, not per-backend.
- Frontend components are plain `.js` + `.css` objects (`{ template, props, setup }`)
  that `import './styles.css'` (the self-written bundler inlines CSS via a `<style>`
  injection). Use **relative imports** (the bundler does not resolve `@/`).
- `node_modules/.bin/{vite,vitest}` shims are broken in this checkout (they do
  `import './dist/cli.js'`); invoke directly: `node node_modules/vitest/vitest.mjs`
  and `node node_modules/vite/bin/vite.js`.
- `common_components/input_datetime_range/index.js` has an inverted `isValidDate`
  ternary in `fromInputValue`, so datetime-range filtering is broken; RecordsFilter
  currently avoids `date`/`datetime` columns (the projects list uses `text` for
  `created_at`/`modified_at`).

## Open questions / TODO

- Compound scalar types (object with named fields, collection, tuple) still being
  finalized.
- SQLite is the "default" only by convention (docs/examples); there is no fallback.
  Decide whether SQLite should auto-create a missing file instead of requiring it
  to exist (currently it matches YAML's fail-early behavior).
- `.db` extension is intentionally **not** mapped to SQLite (ambiguous); add it
  only if a concrete need appears.
- The UI only *lists* QC rules so far; the rule CRUD UI (add/edit/delete/rename) is
  not implemented yet — the `/qcrules` endpoints exist and are exercised by
  `tests/test_endpoints_rule_crud.py`, but the frontend doesn't call them yet.


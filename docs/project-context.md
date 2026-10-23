# Project context

> Living document. Updated after every task. Read this first at the start of every task.

## Last state

- Implemented the "Tests runner" (roadmap item). Added a global cmdlet registry
  package `src/cmdlets/` (`registry.py` + `sysmissing.py` sentinel +
  `builtin_cmdlets.py` with `literal`/`count` + `comparison_ops.py` with
  `eq`/`ne`/`lt`/`le`/`gt`/`ge`/`contains`), and a single top-level runner
  `src/rule_runner.py` (`run_rule(rule) -> bool`): runs the `left` chain, the
  `right` chain, then the comparison `op`; returns `False` on a false comparison
  and raises on any error. Wired `Rule.run()` to delegate to it (single source of
  truth), made `tstsuite.run_tst_case` raise `AssertionError` on a false result,
  exposed `run_rule` on `config.iface` in `main_ui_program.py`, and added a
  `POST /functionality/run-rule` endpoint (`frontend/endpoints_rule_run.py`) that
  runs arbitrary rule JSON (deliberately outside the `/qcrules/...` DB-resource
  namespace) and returns a 4xx + the exception message on error. Created
  `docs/cmdlet-data-formats.md` — a draft spec of the cmdlet value type system
  (scalars + `sysmissing` + block / named collection / loop-grid-array) to review
  before building the full cmdlet set on top of it.

- Renamed the frontend "projects list" (which is actually the QC-rule list) to
  `app/qcrules_list/`: directory, `QcRulesList` component, registration
  `component-qcrules-list`, and CSS classes `apqa-qcrules-list*` (previously
  `apqa-projects-list*`). `app.js` now imports/registers `QcRulesList` under
  `apqa-app-section-qcrules`. "project" is now reserved for an actual project
  list. Updated `records_filter/README.md` and `docs/project-context.md`.
- Added a **Markers** multi-punch filter to the QC rules list: `COLUMNS.markers`
  (options derived from the loaded records, like `tags`) so a user can filter to
  rules with `skip`/`xfail` markers. `toRecord` already exposed `markers`.
- Column defs now carry an optional `description` ("docstring"); `RecordsFilter`
  preserves it in `columnsSanitized` (not rendered yet) for a future per-column
  help message. `COLUMNS` in `qcrules_list/index.js` now includes descriptions.
  Documented `description` in `records_filter/README.md` and added a spec.
- Changed the multi-punch filter semantics from "any selected tag" (OR) to
  "all selected tags" (AND), so it behaves like the other filter boxes (each is
  AND-ed together). `matchMultipunch` now uses `selected.every(...)` against the
  record's value set; empty selection still matches everything. Updated
  `matchers.spec.js` (36 tests) and the `records_filter/README.md` matching note.
  Validated: 45 project JS tests pass.
- Fixed the multi-punch dropdown misalignment. Root cause: the RecordsFilter
  field styling selector `.apqa-records-filter-field input` was broad enough to
  hit the checkboxes inside the child `component-multipunch` (forcing them to
  `width: 100%` + input padding/border). Scoped it to
  `input:not([type="checkbox"]):not([type="radio"])` in
  `records_filter/styles.css` (both the box and `:focus` rules), so text and
  number/date range inputs keep their styling while the multi-select checkboxes
  stay native-size. Validated `vite build` (63 modules) and the self-written
  `pack_js` bundle (contains the scoped selector).
- Follow-up on the Tags multi-punch dropdown: investigated a layout/compactness
  complaint and confirmed `src/frontend/template/templates/common.css` is **not**
  the cause (its checkbox/label/input rules are all scoped to
  `.mdmreport-controls`, which the dropdown never uses), so `common.css` was left
  untouched. Made the dropdown compact in its own
  `common_components/multipunch/styles.css` (menu padding 4→2px, option padding
  `5px 6px`→`2px 6px`, option gap 8→6px, `line-height: 1.2`, checkbox
  `flex: 0 0 auto` + `accent-color`). Added a forward-looking rule
  `.clinerules/09-frontend-common-css.md`: `common.css` is the global skin — fix
  per-component layout in the component `.css`, and any change to `common.css`
  must be logged with date + reason in
  `src/frontend/template/templates/common.css.changelog.md` (created, seeded with
  "no changes yet"). The same policy is noted in `docs/development.md`.
- Implemented the "Tags" multi-punch filter (roadmap item). Added a **global**
  multi-select component at `common_components/multipunch/index.js`, registered
  as `component-multipunch` in `app.js`. It is a single-line trigger that opens a
  checkbox list on click and closes on an outside `pointerdown`; value is an
  array (`v-model`), `options` may be strings or `{ value, label }` objects.
  `RecordsFilter` now supports column `type: 'multipunch'` with an `options`
  array (sanitized `columns` preserve `options`; `filters` init a multipunch key
  to `[]`); it renders the global component for those columns. `matchers.js`
  gained `matchMultipunch` (matches when the record has *all* selected values;
  empty selection matches everything) and multipunch-aware `summarizeFilters`.
  `qcrules_list` sets `tags` to `type: 'multipunch'`, keeps `meta.tags` as an
  array in `toRecord`, and computes the allowed tag options from the loaded
  records; `rule.js` renders `record.tags.join(', ')`. Removed the done roadmap
  item. Validated: 45 project JS tests pass (5 new multipunch + 36 matchers + 4
  records_filter), full `vitest` 60 passed (the 4 `src/lib/myers-diff` suites
  still fail pre-existing), `vite build` transforms 63 modules, and the
  self-written `py_js_bundler` `pack_js` still bundles `app.js` (bundle contains
  `apqa-multipunch` / `component-multipunch`).
- Fixed cmdlet-chain word wrapping. The chain no longer uses
  `word-break: break-all` (which broke words mid-token). `cmdlet.js` now
  exposes `cmdletParts(cmdlet)` (name + each argument as separate units;
  `cmdletText()` = `cmdletParts().join(' ')`) and the `Cmdlet` component renders
  each part as a no-wrap `.apqa-cmdlet-part`; the chain wraps between parts and
  ellipsizes overlong parts (long `path=` params cut on the right). Kept the
  style local to `qcrules_list/styles.css` (the report `common.css` is a
  separate skin; a shared utility class can be extracted later if a second
  consumer appears). Left the "Windows Explorer-style path truncation" idea in
  the roadmap. Added `cmdletParts` tests.

- Made the **RecordsFilter** component collapsible into a compact one-line
  header. It now starts **collapsed**: a clickable header
  (`.apqa-records-filter-header`) shows `▸ Filter` plus a summary of any active
  filters (e.g. `Name: alps · Year: 2020..2025`) in both collapsed and expanded
  states; clicking it expands the full
  filter boxes + sort/pagination toolbar (left visually unchanged) and clicking
  again collapses. Added a pure `summarizeFilters(filters, columns)` helper to
  `matchers.js` (text → trimmed value; number/date/datetime ranges →
  `from..to` / `≥ from` / `≤ to` with local `Date` formatting). Added
  `records_filter/index.spec.js` (component toggle + summary) and extended
  `matchers.spec.js`. Removed the now-done roadmap item. Validated: 45 project
  JS tests pass; `vite build` transforms 61 modules with no errors. (The 4
  failing `src/lib/myers-diff` suites are pre-existing and unrelated.)

- Added a **compact QC-rule representation** alongside the existing full view.
  Decision: **two separate components**, not one parametrized component — the
  full `app/qcrules_list/rule.js` stays as-is and a new
  `app/qcrules_list/rule_compact.js` renders the compact view (one description
  line = name + optional comment, one definition line = left chain · comparison
  op · right chain). Both reuse `cmdlet_chain.js` and `comparison.js`; compact
  styles (`.apqa-rule-compact*`) were added to `styles.css` and covered by
  `rule_compact.spec.js` (a `@vue/test-utils` mount test). **Default for future
  rule-list panes is the compact view**; the current `qcrules_list` still uses
  the full view until such a pane is built. Validated: 4 JS spec files (34 tests)
  pass; `vite build` transforms 61 modules with no errors.

- Removed the `enabled` field from QC rules (roadmap item). It was never a
  dedicated DB column — it lived in `meta` — but it is now gone from the model
  docs, the YAML/SQLite test fixtures, and the UI (`COLUMNS`, `toRecord`, the
  "enabled/disabled" badge, and its CSS). Disabling a rule is now expressed as a
  pytest modifier in `meta.markers`: `skip` means "do not run". Added
  `src/tstsuite.py` helpers `markers_for`, `pytest_param_for`, and
  `load_case_params` so the bundle's parametrized entry point maps
  `skip`→`pytest.mark.skip` and `xfail`→`pytest.mark.xfail` (strict=False); the
  bundle's `build.sh` appended code now uses `load_case_params()`. Added
  `tests/test_tstsuite.py`; full suite 63 passed, JS suite 6 passed.

- Decided the frontend canonical date type and fixed the datetime-range
  comparison. Added a `.clinerules/06-dates-and-time.md` rule: inside
  `src/frontend/app_js`, dates/timestamps are native `Date` objects (built with
  `new Date(...)`), never ISO strings; convert at the data boundary and at the
  native `<input type="datetime-local">` boundary. Fixed
  `filter_records_form/match/datetime_range.js` (was comparing `>=`/`<=` against
  `Date` bounds with a possibly-string `fieldValue`; now normalizes to `Date` and
  compares via `.getTime()`). Fixed
  `input_datetime_range/component_widget_window.js` (the `datetime-local` picker
  returned strings; now converts to/from `Date` at that boundary so the
  component always emits `Date` objects) and `input_datetime_range/index.js`
  (`toInputValue` now formats `Date` endpoints as local `YYYY-MM-DDTHH:mm`).
  Added `filter_records_form/match/datetime_range.spec.js`; JS suite 32 passed.

- Added `/functionality/...` endpoints in a new `src/frontend/endpoints_functionality.py`
  (`handle_functionality`, registered as `re.compile(r'^/functionality(?=$|/)')`).
  `GET /functionality/config` returns the root config as JSON with `iface` dropped
  (callables/classes/DBFile handle are not meant for JSON) and datetimes ISO-ified via
  the existing `JSONEncoder` (UTC-aware `time_start` → `...+00:00`). Help text is no
  longer part of the config: `main_ui_program.py` now exposes `get_help_pages()` in
  `config['iface']` (a callback closing over the already-imported `help_md`), served by
  `GET /functionality/help-pages` as `{"help_pages": <md>}`. `render_page_help` (`/help`)
  now fetches `/functionality/help-pages` instead of reading `config.help_pages`. Added
  `tests/test_endpoints_functionality.py`; full suite 58 passed.

- Fixed the blank bundle version. `build.sh` generated `src/GENERATED/VERSION.py` via
  plain `git describe`, which emitted nothing when no annotated tag was reachable from
  HEAD (and silently swallowed the failure because the pipeline had no `pipefail`).
  Now it uses `git describe --tags --long --always --dirty`: `--tags` also matches
  lightweight tags, `--long` always prints the commit-count + short hash (even when
  exactly on a tag), `--always` falls back to the bare commit hash when there are no
  tags, and `--dirty` appends `-dirty` when the working tree differs from the commit.
  A non-git / no-tags fallback of `unknown` is set explicitly so `_VERSION` is never
  empty. `git fetch --tags || true` was already present.

- Fixed `header.header` rendering shorter than its `.container` child (its bottom
  border was cutting into the navbar's bottom padding). Cause: the always-empty
  `.banner-global-folder-props` placeholder had `margin-top: -7px; margin-bottom: -7px`,
  which made the header's flex-basis (auto/content size) compute ~6px smaller than the
  actually-rendered content. Changed it to `margin: 0`; the header now wraps its
  content (37.5px instead of 23.5px) and leaves proper space below the navbar links.

- Addressed the "Format navbar links" roadmap item. In `src/frontend/project_specific.css`
  the navbar rules were moved from the stale `gitgui-*` classnames to the real
  `apqaui-*` markup classes (right-aligned links via `margin-right: auto` on the page
  name, `list-style-type: none`, and fixed the invalid `flex-wrap: true` → `wrap`).
  Fixed the in-page popup layer in `src/frontend/app_js`:
  `app/background_navlinks_attachmodals/window_component.js` now uses `apqa-*` classes
  (matching `common_components/modals/styles.css`), and the modal was made to fill most
  of the viewport (`top`/`bottom: 24px`, flex column) with a scrollable content iframe
  and a pinned Close button — so an embedded page scrolls inside the popup while the
  fixed backdrop still lets the page behind scroll.

- Consolidated the report CSS into a single `src/frontend/template/templates/common.css`
  by adopting the updated `gitgui` version, which already merges the old
  `common.css` + `common_tables.css` into one file (adds a `:root` token scale,
  `.mdm-btn*` / `.mdm-link*` / `.mdm-table*` components, and refactors spacing to CSS
  variables). Deleted `common_tables.css` and removed its read in
  `build_templates.py build_common_css()` (now reads only `common.css`). Verified the
  `common_css` build resource still minifies (15,210 bytes).

- Made the `run_*.sh` / `run_*.bat` scripts work from the repo root: they launch the
  program via `python -m src.launcher` and point at `tests-real-sensitive-data/`.
  `build.sh` now transforms them for `dist/` (`-m src.launcher` → `apqa_bundle.py`,
  `dist/apqa_bundle.py` → `apqa_bundle.py`, `tests-real-sensitive-data/` →
  `../tests-real-sensitive-data/`, and the dev-only "build the bundle first" block in
  `run_tests.*` is stripped). `run_tests.*` stay bundle-only: from the root they run
  `build.sh` first, then pytest on `dist/apqa_bundle.py`.

- Resolved the "Review if `@` alias is working in frontend" TODO: the self-written
  JS bundler **does** resolve the `@` alias (app root, from `jsconfig.json`
  `compilerOptions.paths`). Verified by swapping a deep `../../` for `@` and
  building the JS distributable successfully. Relative imports remain the default in
  JS (self-contained, liftable components); use `@/...` when reaching up to an outer
  level. Removed the stale "bundler does not resolve `@/`" note below and the roadmap
  item.

- Removed the **`repoActions` layer + prop-drilling** (copied from another
  project). `useErrorReporting()` now returns only `{ errors }`; `app.js` no longer
  builds/passes `repoActions`; components import the module-level singletons
  directly — `logError` from `common_components/_log_error_proxy` and `createModal`
  from `common_components/modals/modals` (the same deferred-resolution pattern
  already used by `logErr` throughout `common_components`).
- Fixed the inverted `isValidDate` ternary in
  `common_components/input_datetime_range/index.js` (`fromInputValue`): valid dates
  now stay `Date`s and invalid ones become `null`; also added the missing `logErr`
  import in `common_components/filter_records_form/index.js`.
- Implemented the **UI "QC rules list"** in `src/frontend/app_js`: the list of QC
  rules (the home page is literally "Manage QC rule list"; here "projects" == the
  QC-rule records). `app/qcrules_list/index.js` fetches `GET /qcrules` and
  flattens each rule into a filterable record (`name`, `op`, `comment`,
  `tags`, `created_at`, `modified_at`, plus raw `left`/`right` cmdlet arrays).
- Refactored the rule rendering into modular components under `app/qcrules_list/`:
  `rule.js` (Rule), `cmdlet_chain.js` (CmdletChain), `cmdlet.js` (Cmdlet, with a
  renderer registry — `registerCmdletRenderer` — so specific cmdlets can override
  rendering; the `literal` cmdlet renders just its value), and `comparison.js`
  (Comparison, which maps ops to symbols: `eq`→`=`, `lt`→`<`, `gt`→`>`, …). The
  rule definition is a 3-column grid (`1fr max-content 1fr`) with left/right
  top-aligned; `created_at` renders through `format_datetime` (`new Date(…)`, local
  time) per `.clinerules/06-dates-and-time.md`. Pure helpers `cmdletText` and
  `comparisonSymbol` are unit-tested in `cmdlet.spec.js`.
- Ported the **RecordsFilter** component from apphotoassistant
  (`frontend/src/components/records-filter/RecordsFilter.vue`) into
  `common_components/records_filter/` as plain `.js` + `.css` (no `.vue`):
  `index.js` (Vue component), `matchers.js` (pure match/sort), `matchers.spec.js`
  (22 vitest tests, all passing), `styles.css`, `README.md`. It keeps the
  **two-level filtering** (css-class `.apqa-u-hidden` for recently-hidden records +
  physical removal after a 5-min TTL) so records aren't destroyed while the user is
  typing. The QC rules list is wrapped in it.
- Added an **error banner** (`app/apppane_errorview/`) plus an error-reporting
  composable (`common_app_exposed_defs/error_reporting/index.js`) that wires the
  existing `common_components/_log_error_proxy` (resolves `promiseResolve`).
- Wired everything in `app.js` (root template now renders the error banner, the
  QC rules list, `background-navlinks-attachmodals` and `modals-site`; sets up
  `useErrorReporting`). Added a `/qcrules` proxy entry to `vite.config.js` for dev
  mode.
- Validated: `matchers.spec.js` (22) + `cmdlet.spec.js` (6) tests pass; the
  self-written `py_js_bundler` bundles `app.js`; `vite build` transforms 61 modules
  with no errors.

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

- `src/launcher.py` must be run as `python -m src.launcher` (its `__main__` branch
  imports `src.GENERATED.*`, which needs the repo root on `sys.path`); `python
  src/launcher.py` fails with `ModuleNotFoundError: No module named 'src'`.
- The `run_*.sh`/`run_*.bat` scripts are root-oriented (launch `-m src.launcher`, use
  `tests-real-sensitive-data/`); `build.sh` rewrites them for `dist/` via
  `build_templates.py --program transform-run-script` (`-m src.launcher` →
  `apqa_bundle.py`, data path → `../tests-real-sensitive-data/`, strips the
  `run_tests.*` build block). `run_tests.*` are bundle-only: from the root they run
  `build.sh` first, then pytest on `dist/apqa_bundle.py`.

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
  injection). Prefer **relative imports** (self-contained, liftable components); the
  self-written bundler *does* resolve the `@` alias (app root, from `jsconfig.json`
  `compilerOptions.paths`), so use `@/...` instead of deep `../../..` when reaching
  up to an outer level.
- `node_modules/.bin/{vite,vitest}` shims are broken in this checkout (they do
  `import './dist/cli.js'`); invoke directly: `node node_modules/vitest/vitest.mjs`
  and `node node_modules/vite/bin/vite.js`.
- RecordsFilter currently avoids `date`/`datetime` columns (the QC rules list uses
  `text` for `created_at`/`modified_at`). The canonical date type is now `Date`
  objects (see `.clinerules/06-dates-and-time.md`); the range inputs emit `Date`
  objects and the matchers normalize to `.getTime()`. Enabling `date`/`datetime`
  columns still needs end-to-end wiring (build record fields as `Date` objects in
  `qcrules_list/toRecord`).

## Open questions / TODO

- End-to-end datetime-range filtering is still not wired in the QC rules list
  (`created_at`/`modified_at` remain `text` columns). The canonical value type is
  decided (`Date` objects) and the range inputs/matchers now comply, so wiring
  `date`/`datetime` columns should just mean building record fields as `Date`
  objects in `qcrules_list/toRecord`.
- The cmdlet value type system is **not yet implemented** — the runner and
  comparison ops work on plain Python values plus the `sysmissing` sentinel. A
  draft spec lives in `docs/cmdlet-data-formats.md` (scalars, `sysmissing`,
  block / named collection / loop-grid-array) and awaits review. The full cmdlet
  set (source readers, `select-*`, `map`, `to-string`, …) will be built on top of
  it once aligned — the current built-ins are only `literal` and `count`.
- SQLite is the "default" only by convention (docs/examples); there is no fallback.
  Decide whether SQLite should auto-create a missing file instead of requiring it
  to exist (currently it matches YAML's fail-early behavior).
- `.db` extension is intentionally **not** mapped to SQLite (ambiguous); add it
  only if a concrete need appears.
- The UI only *lists* QC rules so far; the rule CRUD UI (add/edit/delete/rename) is
  not implemented yet — the `/qcrules` endpoints exist and are exercised by
  `tests/test_endpoints_rule_crud.py`, but the frontend doesn't call them yet.


# Project context

> Living document. Updated after every task. Read this first at the start of every task.

## Last state

- **Cleaned unnecessary deep upward imports in the frontend JS.** Replaced the
  `../../common_components/...` and `../../common_defs/...` imports (2 levels up,
  reaching shared components/defs placed relative to the app root) with the `@/...`
  alias (`@` → `src/frontend/app_js/src`, per `jsconfig.json`/`vite.config.js`).
  Files touched: `src/app/qcrules_list/{rule_form,rule_edit_form,index,rule}.js`,
  `src/app/background_navlinks_attachmodals/manipulate_links.js`, and
  `src/common_app_exposed_defs/error_reporting/index.js` (17 import lines). The
  single-level `../` sibling references *within* `common_components` (e.g.
  `../_log_error_proxy`, `../input_multipunch`) were left as-is — those are genuine
  component-to-sibling encapsulation, not app-root references. Confirmed the
  self-written bundler resolves `@/` on the real entry point (`process('…/app.js')`
  → 222,284 chars) and the bundler integration test passes (7/7); Vitest is 146/146
  across 19 files. Precedent already existed (`apppane_errorview/index.js` and
  `background_navlinks_attachmodals/window_component.js` already used `@/`).

- **Removed the unused `myers-diff` vendored package (roadmap item).** It lived at
  `src/frontend/app_js/src/lib/myers-diff/`, was never imported by the app, and its 4
  mocha/chai test suites were being picked up by Vitest (`test/*.test.js`) and failing
  on a module-resolution error: the package's own `src/index.js` uses an extensionless
  ESM import (`import { diff } from './myers'`), which Vitest's native ESM resolver
  rejects (`Cannot find module '.../src/myers'`). So it was neither a typo in our code
  nor a `py_js_bundler` bug — it is obsolete third-party code written for a
  bundler/CommonJS-mocha setup; removed entirely (trivial to re-add if a real diff
  use-case ever appears). Verified safe re: submodules — `myers-diff` is **not** in
  `.gitmodules` (only `pinliner`, `webserve`, `py_js_bundler` are) and is tracked as
  plain files, not a gitlink; its stray `myers-diff/.git` gitfile (a leftover from its
  submodule past in `gitgui`) pointed at a non-existent `.git/modules/...` path and was
  removed with the directory. Full frontend suite is now **146 passed across 19 files**,
  no myers-diff. Gotcha: in this checkout `node_modules/.bin/vitest` is a flattened
  regular file (not a symlink), so `npm run test:unit` fails before running any tests
  (`Cannot find module '.../node_modules/.bin/dist/cli.js'`); I ran
  `node node_modules/vitest/vitest.mjs run` instead — fix with `npm ci`/`npm install`.
- **Implemented in-place "Edit rule" (roadmap item).** Clicking Edit now swaps the
  expanded rule's display for an inline form (`rule_edit_form.js`) inside the same
  rule container, pre-filled from the stored record (`name`, read-only `id`,
  `comment`, `tags`, `markers`, `left`/`right` cmdlet chains, `op`/`op_args`).
  The form has explicit **Save**/**Cancel**; Save does `PUT /qc/rules/<id>` with
  only the form-managed fields, merged back into the preserved `meta` (so `order`,
  `created_at`/`modified_at` and unknown keys survive), then reloads. `toRecord`
  now carries `op_args` + a full `meta` copy so the editor round-trips them.
  Editing state is lifted to the page as a single `editingId`, threaded
  rule_body → rule_record → rules_tree → page. **Guard against losing unsaved
  edits:** `RulesTree` refuses to collapse a folder that contains the edited rule,
  refuses pagination while editing (a `window.alert` warning), and skips its normal
  re-fold-on-groups-change while `editingId` is set. Only one rule can be edited
  at a time (`onEditRule` warns and blocks switching). Gotcha fixed: a Boolean
  `editing` prop must be a real boolean — the computed returning `''`/truthy was
  cast to `true` by Vue's Boolean-prop casting.

- **QC-rules list: physical marks + shared tree-entry base class.** Rule leaves and
  folder headings share `.apqa-rules-tree-item` (indent/list flow), with
  `.apqa-rule-record` / `.apqa-rules-tree-group` kept as kind markers. `grouping.js`
  now derives a physical `unfinished` mark when **any** of left / op / right is
  missing (`isUnfinished`); `markNamesForRecord` returns stored markers + that
  derived mark, and `markClassesForRecord` maps them to short CSS classes. Every
  rule (compact + full) renders a final badge line (`marks_badges.js`) and an
  unfinished rule gets a grey helper note under its name + a `title` tooltip on the
  badge. Folders render "includes rules marked …" with aggregated badges/classes
  (`groupMarks` / `groupMarkClasses`). `tstsuite.pytest_param_for` now skips
  unfinished rules at run time. Highlighting precedence is still provisional
  `unfinished` > `skip` > `xfail`. Documented in `docs/development.md` "Markers".

- **Rule ids are now enforced unique on create (roadmap item).** Previously
  `DBFile.add_rule` silently auto-deduplicated a colliding id (`-2`, `-3`, …);
  now the backend rejects a duplicate rule id with a `ValueError`
  (`_ensure_rule_id_available` on `DBFile`, used by both the YAML and SQLite
  backends), which `POST /qc/rules` surfaces as a `400`. The dedup moved to the
  UI: `rule_form.js` gained `makeUniqueSlug`/`ensureUnique` (mirrors of
  `ids.py`), the form receives `existingIds` from the page and (a) auto-fills a
  unique slug from the display name, (b) re-generates a unique slug when the id
  is cleared, and (c) shows an inline error instead of submitting when a
  manually-entered id collides. Groups are unchanged (their generated id is
  still auto-deduplicated on add). Updated Python tests (yaml/sqlite crud,
  endpoints) and the `rule_form` Vitest spec.

- Renamed the multi-punch dropdown component `multipunch` → `input_multipunch` to
  match the other `input_*` controls. Global registration
  `component-multipunch` → `component-input-multipunch`, local usage
  `multipunch` → `input-multipunch`, and CSS `apqa-multipunch-*` →
  `apqa-input-multipunch-*`. Updated consumers (`records_filter`,
  `input_qcrule_marks`) and their specs.

- Added a **Delete rule** action to the QC-rules list. Each expanded rule row now
  shows an explicit "Delete" button next to "Edit"/"Run" (neutral by default,
  red on hover — not inviting to click). Clicking it opens a small centered
  confirmation modal (`rule_delete_confirm`) that names the rule and warns it
  cannot be undone; confirming calls the existing `DELETE /qc/rules/<id>`
  endpoint and reloads the list. The `delete` event is forwarded up
  rule_body → rule_record → rules_tree → the page. Backend already had the
  endpoint + `DBFile.delete_rule`, so this is frontend-only. Tests updated/added
  (`rule_record`, `rules_tree`, `rule_delete_confirm`).

- Added a **searchable single-select drop-down** component
  (`src/frontend/app_js/src/common_components/input_search_select/`) and wired it into
  the cmdlet selector (`input_cmdlet`), replacing the native `<select>`. The new
  control's search box is focused by default when the drop-down opens; typing
  filters the pre-defined options (case-insensitive substring), arrow keys move
  the highlight and Enter selects. It only allows choosing from the list (no
  free-form value). Registered globally as `component-input-search-select` in `app.js`
  and imported locally in `input_cmdlet` (same pattern as `input_multipunch`). Updated
  `input_cmdlet`/`input_cmdlet_chain` specs and added an `input_search_select` spec; all
  app/common-components specs pass (the 4 `myers-diff` suites fail on a
  pre-existing module-resolution error, unrelated). Follow-up fix: removed the
  `opacity: 0.85` on the trailing chain slot — it made the open menu translucent
  and created a stacking context that let a lower dropdown render on top.

- **Implemented "create QC rule" as a modal form.** The green "Create new QC
  rule" button now opens a modal (the existing `createModal` system) with **one
  input per rule field**: the auto-filled technical name (`id`, shown first — a
  slug mirroring `src/db_processors/ids.py:make_slug`, which stops following the
  display name once the user edits it), the display `name` (required),
  `meta.comment`, `meta.tags`, `meta.markers`, the `left`/`right` **cmdlet
  chains**, and the `op`/`op_args` comparison (`meta.order` is not exposed — on
  create the page sets it to `max(existing order) + 1` so the new rule is
  appended last). New rules are created at the top level
  (`group: ''`) for now; dragging a rule into a folder is a later flow. To feed
  the form, cmdlets and
  comparison ops now carry **editor metadata** declared next to each
  registration: a cmdlet has a `kind` (`source` = can be first in a chain,
  `processor`, or `terminal`) and an `args` schema (`name`, `type`, `required`,
  `default`, `description`); an op carries `op_args` schemas. The registry
  `register(...)` decorators store this (`src/cmdlets/registry.py`,
  `src/cmdlets/comparison_ops.py`) and a new
  `GET /functionality/cmdlet-metadata` endpoint (`src/cmdlets/meta.py`, exposed
  through `config['iface']`) serves `{ cmdlets, ops }`. New app-level input
  components live in `src/frontend/app_js/src/common_components/` and all follow
  the native input contract (`v-model`/`modelValue` + `update:modelValue` +
  `input`/`change`): `input_cmdlet`, `input_cmdlet_chain`, `input_comparison_op`,
  `input_qcrule_tags`, `input_qcrule_marks`. Cmdlet **arg types**: `text`
  (default), `number`, `boolean`, `path`, `options`, `list`, `json`
  (`literal.value`), and `cmdlet-chains` (a list of chains, e.g.
  `and`/`or`/`bit-*` `operands`). `input_cmdlet_chain` offers source readers
  first and processors/terminals afterwards, always showing a trailing
  placeholder for the next cmdlet. Tests: `tests/test_cmdlet_metadata.py` plus
  five new Vitest specs; full Python suite 641 passed.


- Added a **CLI storage initializer** (`--program init`, new
  `src/main_init_program.py`) that creates an empty QC-rules storage at a given
  path. It parses a required `--db-file` and an optional `--db-format`; the
  format defaults to `detect_type(path)` and is otherwise routed through the
  existing db_processor registry, so every format registered in
  `src/db_processors` (yaml, sqlite, …) is supported with no hardcoded list.
  Creation logic lives in each processor (`DBFileYaml._init_storage` /
  `DBFileSqlite._init_storage`), with a single router
  `DBFile.init_storage(path, type=None)` on the base class; sqlite DDL is now
  shared between fresh creation and the legacy migrations. The init program
  follows `main_ui_program.py`'s coloring/error-reporting style (raise +
  launcher's red error block). `init_storage` refuses to clobber an existing
  file (`FileExistsError`). New tests in `tests/test_db_processors_init.py`;
  289 dev tests pass.

- **Split rule/group `name` into `id` (technical) + `name` (display).** Rules and
  groups now each carry a stable, auto-generated `id` — an ASCII alphanumeric
  slug derived from the display name (`src/db_processors/ids.py`: lower-cased
  words joined by `-`, never starting with a digit, accents folded, fallback
  `rule`/`group`) — plus the free-form, user-visible `name`. References
  (`Rule.group`, `Group.parent`) now use the **group id**, so a display-name
  change (e.g. a future translation) never breaks references. Ids are unique per
  entity type; display names may repeat. (Later changed: adding a rule with an
  existing id now raises, and the UI deduplicates the generated slug; groups
  still auto-deduplicate on add.) `rename_rule`/`rename_group` now change the
  display name only (no
  cascade). Lookups (`get_rule`/`has_rule`/`get_group`/`has_group`, CRUD
  endpoints) take the id; `DBFile.resolve_group_ref()` accepts either an id or a
  display name for incoming references. **Migration**: loading pre-split data
  (YAML `_read`; SQLite table rebuild in `_ensure_schema`) generates `id` from
  the old `name` and remaps old name-based `group`/`parent` references to ids.
  Frontend `qcrules_list` splits `id`/`name` in records, keys the tree by `id`,
  and still shows only `name`; create flows resolve a typed group name → id.
  Tests updated; new `tests/test_ids.py`. **Group aliases are already id-only**:
  an alias `name` is the technical id (variable-name-shaped) — there is no
  separate human-shown name. The real `tests-real-sensitive-data/projects.*`
  files were migrated to the new format.


- Added a `format-strip-html` terminal cmdlet (`src/cmdlets/format_strip_html/__init__.py`,
  registered in `src/cmdlets/__init__.py`) that removes HTML markup and leaves
  plain text (`how <i>would</i> you rate...` → `how would you rate...`). It uses
  `BeautifulSoup(..., "html.parser")`, so misformatted/unbalanced markup is parsed
  best-effort instead of rejected. `sysmissing` → `""`; blocks/arrays recurse and
  keep their shape; other scalars delegate to the existing `as-text`.
  `beautifulsoup4` is an **optional dependency** — a per-cmdlet `requirements.txt`
  (`beautifulsoup4>=4`) plus the guarded-import pattern (the cmdlet is always
  registered and only raises a readable `ImportError` when run without the dep).
  The family prefix `format-` is provisional — see `docs/roadmap.md`. Tests in
  `tests/test_standard_cmdlets.py` + `tests/test_optional_dependencies.py`.


- CSS alignment pass on the QC-rules list (`qcrules_list/styles.css`): narrowed the
  shared entry box's horizontal padding (10px→8px) and the folder-header gap
  (8px→5px), pulled the monospace `[+]` toggle back with `margin-left: -2px`, and
  rendered the `(empty)` chain placeholder in IBM Plex Sans — all so folder titles
  and rule text share the same left indent. `docs/roadmap.md` gained two TODOs
  (decide alias reference syntax; review how `/functionality/run-rule` should
  resolve aliases).

- UI styling pass for folder aliases: removed the alias-row border/padding/box and
  the inter-line gap, so aliases render as tight plain `name: chain` lines below
  the folder name, indented by `var(--mdm-space-0-75x)` (22.5px), in muted grey
  (`#666`) with 2px between name and colon and 6px between colon and chain;
  removed the grey rule under the "QC rules" heading. SQLite `_ensure_schema`
  now `DROP TABLE IF EXISTS definitions` (no backward compat for the removed
  global-definitions table).

- Replaced **global aliases (definitions)** with **folder aliases**. Removed the
  `Definition` entity (`src/db_processors/definition_base.py`), its `DBFile`
  contract (`list_definitions`/…), the `definitions` SQLite table/column writes,
  the YAML top-level `definitions` list, the `/qc/definitions…` endpoint
  (`endpoints_definition_crud.py`), and the frontend "Global aliases" section +
  `definition_record.js`. A `Group` now carries an `aliases` list of
  `{ name, chain, meta }` (a cmdlet chain that produces the value), stored as a
  `groups.aliases` JSON column in SQLite (with an automatic `ALTER TABLE`
  migration) and as a per-group `aliases` list in YAML; `Group.from_dict`/`update`
  normalize them (unique names, `chain` must be a list). New
  `src/group_aliases.py`: `substitute()` (recursive alias-name → resolved-value
  substitution that skips a cmdlet's `cmdlet` key) and `AliasScopeResolver`
  (resolves each folder's aliases once via `run_chain`, caches the scope,
  inherits parent scope, child shadows parent). `src/tstsuite.py` `load_cases()`
  now resolves aliases per rule group and yields a plain list of `Rule` copies
  with resolved chains; ungrouped rules pass through untouched. Frontend:
  `RulesTree` renders folder aliases as `name: chain` rows (new `alias_record.js`)
  under an expanded folder; the "Add alias" button now prompts for folder + name +
  chain JSON and PUTs the group's `aliases`. Tests: removed
  `tests/test_db_processors_definitions.py` and
  `tests/test_endpoints_definition_crud.py`; added `tests/test_group_aliases.py`
  and alias cases in `tests/test_db_processors_groups.py` +
  `tests/test_endpoints_group_crud.py` + `grouping.spec.js`/`rules_tree.spec.js`.
  599 Python tests + qcrules frontend tests pass. Sample
  `tests-real-sensitive-data/projects.yaml`/`.sqlite3` now demo aliases on
  `comp titles` and `titles updated`.

- Implemented **foldable rule groups (folders)** — the roadmap "Make foldable
  groups for qc rules" item. Rules can now be organized into a tree of groups
  instead of one flat list. New `Group` entity (`src/db_processors/group_base.py`:
  `name` unique, `parent` = parent group name, `''` = top level, `meta`);
  `Rule` gained a `group` field (`''` = ungrouped). `DBFile` gained a group CRUD
  contract (`list_groups`/`get_group`/`has_group`/`add_group`/`update_group`/
  `rename_group`/`delete_group` + `.groups` accessor + `_validate_group_parent`
  that fails early on missing parent / self-parent / cycles). SQLite: new
  `groups` table and a `"group"` column on `rules` (quoted — `GROUP` is a SQL
  keyword); rename cascades to child `groups.parent` and `rules.group`; delete
  refuses a non-empty group. YAML: new top-level `groups` list (read/write), same
  semantics. New `/qc/groups…` CRUD endpoint (`endpoints_group_crud.py`) wired in
  `src/endpoints.py` + `src/frontend/endpoints.py`; `/qc/rules` create/update now
  validates that `group` exists. Frontend: `RulesTree` component
  (`qcrules_list/rules_tree.js` + pure `grouping.js`) renders a foldable,
  depth-indented tree (flat DFS + a reactive collapsed set — no recursion in the
  template); rules reuse `rule-record`; ungrouped rules appear at the top level
  (no "Ungrouped" wrapper) and folder headings are a simple `[+]/[-]` outline
  with no rule counter — **all folders start folded**. Rule rows and folders
  physically share the `.apqa-qcrules-entry` box class (border/radius/background/
  padding) and are distinguished by `.apqa-qcrules-entry-rule` vs
  `.apqa-qcrules-entry-folder` (currently empty → everything renders uniformly
  white; add per-kind styling there later). Sibling folders and rules within a folder are interleaved
  by an optional `meta.order` integer (`grouping.js` merges sub-folders + direct
  rules into one sequence and sorts by it; ties keep insertion order). The
  `RecordsFilter` still filters/sorts (its own pagination is disabled via
  `records-per-page=0`), while `RulesTree` paginates the *visible node list*
  (folder headings and rule leaves alike) at `records-per-page=25`, so pagination
  remains the standard pattern for many rules in a folder or many folders at a
  level. "Create group" button + optional group prompt on rule creation added.
  Tests: `tests/test_db_processors_groups.py`, `tests/test_endpoints_group_crud.py`,
  group-validation cases in `tests/test_endpoints_rule_crud.py`, and frontend
  `grouping.spec.js` + `rules_tree.spec.js`. 622 Python tests + 28 qcrules
  frontend tests pass.
  Also populated the sample project files `tests-real-sensitive-data/projects.yaml`
  and `tests-real-sensitive-data/projects.sqlite3` with the example folder/rule
  hierarchy (gitignored, never committed).
  Note: rule *editing/moving* UI (and thus moving existing rules between groups)
  is still a separate roadmap item, so deleting a non-empty group is refused
  until then.

- Added the **`get-content-mdd`** source-reader cmdlet
  (`src/cmdlets/get_content_mdd/`, registered as `get-content-mdd`, optional
  dependency `pywin32` — Windows-only) that reads an MDD metadata document via
  the `MDM.Document` COM API and returns a hierarchical block (sections
  `source_file`, `languages`, `shared_lists`, `fields`, `pages`, `routing`).
  Fields/categories are recursive: `ObjectTypeValue` 0 → scalar, 1/2 → array,
  3 → block; scalars have `value = None` (MDD metadata has no data value) and
  categorical scalars expose their available options as the keys of a
  `categories` name→block map; shared-list references honor a `step_into` arg
  (step into vs step over); label/property contexts are collected across the
  configured `contexts` (default Question/Analysis) following `mdmreadpy`.
  Pure helpers tested in `tests/test_get_content_mdd.py`; registry/optional-dep
  coverage in `tests/test_optional_dependencies.py`; spec in
  `docs/cmdlet-data-formats.md` "Source readers". Not runnable here (needs
  Windows + MDM + pywin32).

- Added a set of **standard scalar cmdlets**: type conversions
  (`as-text`, `as-integer`, `as-real`, `as-boolean`, `as-path`, `as-date` — the
  `as-` prefix delegates to Python's natural conversion; `as-date` resolves the
  timezone from the value or `args['tz']` (IANA name or UTC offset) and fails
  only when it can't), logical operators (`not`,
  `and`, `or`, `any`, `all` — `and`/`or` combine operand cmdlet chains in
  `args['operands']`, all coerce operands to boolean, `sysmissing` → `false`),
  bitwise operators (`bit-not`, `bit-and`, `bit-or`, `bit-xor`, `bit-lshift`,
  `bit-rshift` — integer-only),
  and string helpers (`length`, `matches` with `pattern`/`case_insensitive`/
  `regex` args). Moved `run_chain` from `src/rule_runner.py` into
  `src/cmdlets/chain_runner.py` (with `src/cmdlets/operands.py` helpers) so
  operand cmdlets can run sub-chains without a circular import. Updated `count`
  so empty text counts as `0` (consistent with `as-boolean`). Documented in
  `docs/cmdlet-data-formats.md`; tested in `tests/test_standard_cmdlets.py`.

- Restructured cmdlets to **one folder per cmdlet**: split `literal`, `count`,
  and `sort` out of the removed `src/cmdlets/builtin_cmdlets.py` into their own
  `src/cmdlets/<name>/__init__.py` folders, so every cmdlet follows the same
  self-contained, liftable pattern as `get_content_excel` and
  `validate_xml_compatible` ("built-in" is now expressed structurally — a folder
  with no `requirements.txt`). Added a terminal predicate cmdlet
  **`is-sysmissing`** (`src/cmdlets/is_sysmissing/`) returning `True` iff the
  value is `None`; it does not recurse, so `""`/`{}`/`[]`/`0`/`False` and a
  compound whose fields are all `sysmissing` are not sysmissing. Documented the
  new `is-` predicate group in `docs/cmdlet-data-formats.md`; tests in
  `tests/test_cmdlets.py`.

- Made `count` explicit about what it counts: array → iterations (`len`),
  block / named collection → fields (`len`), text → `1` (never counted
  character-by-character), any other scalar (incl. single-punch categorical) →
  `1` when stored, and `sysmissing` → `0` by default with
  `args['fail_on_sysmissing']` opting into an error instead. (A multi-punch
  categorical counts its punched categories; until those value objects exist, a
  punch list is a plain `list` and counts as its length.) Updated `count`'s
  annotation to `PipeValue` and its tests in `tests/test_cmdlets.py`.

- Introduced the **cmdlet value-type taxonomy** (`src/cmdlets/value_types.py`):
  a root `Value` `Protocol` base plus the `Scalar`/`Compound` families, the
  `Block`/`NamedCollection`/`Array` compound `Protocol`s, and scalar-category
  aliases (`Text`, `Integer`, `Real`, `Boolean`, `PathValue`, `DateTime`,
  `CategoricalSingle`, `CategoricalMulti`); `PipeValue = Optional[Value]` is the
  "value or sysmissing" alias. Runtime stays plain Python — these are
  annotation/documentation types, not runtime wrappers. Annotated the cmdlet
  signatures (`literal`, `count`, `sort`, `get-content-excel`,
  `validate-xml-compatible`) accordingly. Documented in
  `docs/cmdlet-data-formats.md`; tested in `tests/test_value_types.py`.

- Added a terminal **`validate-xml-compatible`** cmdlet
  (`src/cmdlets/validate_xml_compatible/`, registered under the `validate-`
  validation prefix) that checks whether a value can be embedded in XML unchanged.
  Only `text` values are validated (wrapped in a dummy root and parsed); every
  other scalar (`sysmissing`, booleans, numbers, dates, paths) is not XML markup
  and simply passes. Blocks/arrays run the same check per field/item and AND the
  results (empty compound = vacuously valid). Follows the optional-dependency
  pattern with a guarded `xml.etree.ElementTree` import (stdlib, so
  `requirements.txt` is comment-only — `build.sh`/`run_init.*` still
  discover/copy/install it as a no-op). Documented in
  `docs/cmdlet-data-formats.md` "Validation cmdlets"; tests in
  `tests/test_cmdlets.py` + `tests/test_optional_dependencies.py`.

- Introduced **optional per-cmdlet dependencies** (encapsulated, best-effort,
  "fail only when used"): each optional cmdlet lives in its own folder
  (`src/cmdlets/get_content_excel/` — a demonstration Excel source reader needing
  `openpyxl` — is the first) with its own `requirements.txt`, and guards its own
  import (`try/except` storing the error) so the module always loads and the
  cmdlet is always registered; its runtime function raises a readable
  `ImportError` (chained to the original) at the start. No global import-error
  machinery (`CmdletUnavailableError`, `register_unavailable`, and
  `discovery.py` were removed). `build.sh` auto-discovers
  `src/cmdlets/**/requirements.txt` and copies them to
  `dist/optional_dependencies/`; `run_init.sh`/`.bat` install them best-effort
  (WARNING, not fatal); `transform-run-script` rewrites `src/cmdlets` →
  `optional_dependencies` in the dist copies. Documented in
  `docs/development.md` and `.clinerules/10-optional-dependencies.md`.

- Implemented order-agnostic array comparison (all three approaches from the
  design pass): comparison ops now take an optional `args` mapping
  (`(left, right, args=None) -> bool`); `eq`/`ne` accept
  `op_args: { unordered_arrays: true }` (recursive multiset array equality); a
  dedicated `eq-unordered` op hard-wires that flag; and a `sort` cmdlet
  (`args.by`, `args.descending`) canonicalizes array order for a strict compare.
  Added `op_args` to the rule model (`Rule`, SQLite column + migration for
  pre-existing DBs, YAML via `from_dict`/`to_dict`, and the runner). Made
  `docs/cmdlet-data-formats.md` the primary spec and aligned
  `docs/development.md` + `.clinerules/05-domain-model.md` (`select-column` →
  `select-property`, plus a pointer to the canonical doc). 166 pytest tests pass.
- Reviewed and tightened the cmdlet data-format spec (`docs/cmdlet-data-formats.md`)
  after a design pass: (1) `eq`/`ne` now compare **compound values deeply** (blocks
  by field name, order-insensitive; arrays in strict position order) while the
  ordering ops stay scalar-only; (2) `named collection` is now marked
  **provisional** (avoid it initially; drop or promote once readers/cmdlets exist);
  (3) duplicate column dedup now follows pandas' default `state.1`/`state.2`
  (was `state_2`/`state_3`); (4) added a **`path`** scalar type (path-aware
  equality); (5) confirmed `args` values are not restricted to strings and can be
  nested chains, and proposed a `map` shape (`args.transform` = a cmdlet chain).
  Implemented recursive deep equality in `src/cmdlets/comparison_ops.py` and added
  tests.
- Changed the UI primary color from purple `#6670bb` to green `#385`
  (`#338855`), hover shade `#217346` (reusing `--mdm-color-green-hover`), and
  light tint `#eaf6ef`. Updated `--mdm-color-primary` in `common.css` plus its
  primary/link-button hover shades, and replaced every hardcoded `#6670bb`
  (and its `#51599f`/`#5560a8`/`#7780cc`/`#f0f1fb` variants) in
  `project_specific.css`, `qcrules_list`, `records_filter`, `multipunch`, and
  `pages` styles. Regenerated the frontend `GENERATED/` assets
  (`build_templates.py --resource common_css/projectspecific_css/app_js`) and
  verified no purple remains in the bundle. Left the periwinkle accent family
  (`#6c78ff`/`#4d56cc` links, `#6a77ff` spinner, `#7067ff` legacy pagination)
  unchanged — a distinct blue accent, not the purple primary.

- Implemented "Reformat the page with qc rules" (roadmap item). Added project-level
  **definitions (aliases)** stored in the same DB file as rules: a `Definition`
  dataclass (`src/db_processors/definition_base.py`) with `name`/`value`/`meta`,
  matching CRUD on `DBFile` (`list_definitions`, `get_definition`, `has_definition`,
  `add_definition`, `update_definition`, `rename_definition`, `delete_definition`,
  plus the `.definitions` accessor). SQLite gained a `definitions` table; YAML now
  reads/writes a `{ definitions: [...], rules: [...] }` mapping while still accepting
  a legacy top-level list (rules only). Added a definitions CRUD endpoint
  (`src/frontend/endpoints_definition_crud.py`) + route, and unified both DB resources
  under a shared `/qc/` namespace (`/qc/rules` and `/qc/definitions`). Reformatted the QC-rules page:
  top toolbar ("Create new QC rule" / "Add alias", both functional via `window.prompt`),
  then a **Global aliases** section (own `RecordsFilter`), then a **QC rules** section.
  Rules now render a `RuleRecord` wrapper (`<li>`) around a `RuleBody` inner wrapper,
  which shows the compact view by default and switches to the full view (plus
  placeholder Edit/Run buttons) when the rule header (name/comment) is clicked; the
  same header collapses it back. `rule.js`/`rule_compact.js` roots changed `<li>` →
  `<div>` (they now nest inside the record `<li>`) and emit `toggle`. Added specs for
  `RuleRecord` and updated `rule_compact.spec.js`. Validated: 144 pytest, 66 JS tests
  pass (4 pre-existing myers-diff suites still fail), `vite build` (67 modules) and the
  self-written `py_js_bundler` both bundle the new components.

- Finalized the cmdlet data-format spec (`docs/cmdlet-data-formats.md`): named the
  compound type **array** (was "loop/grid/array"), chose shape-agnostic cmdlet
  names mirroring PowerShell (`select-property`, `select-properties`,
  `select-item`, `where`, `map`), defined comparison semantics (bool ≠ number,
  numeric text coerces: `"0" == 0` → true, `None`/sysmissing rules), and defined
  missing/duplicate-name rules (provisional names; `state`, `state_2`, … dedup).
  Changed `sysmissing` to be represented as Python `None` (`sysmissing = None`,
  `is_sysmissing(v) := v is None`) and rewrote `comparison_ops.py` to be
  type-strict per the spec (bool distinct from numbers, int/float unify, numeric
  text coerces, ordering/contains with `None` → false, date/time compared
  timezone-aware).

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
  `@DBFile.register(...)` side effect). Generic accessors like `.rules`,
  `.definitions` and `.groups` belong on the base class, not per-backend.
  `"group"` must be quoted in SQLite SQL (`GROUP` is a reserved keyword).
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

- **Alias reference syntax is undecided.** Currently an alias is referenced by an
  exact whole-string match of an argument value (so `"survey_mdd"` is substituted,
  with no way to pass a literal `"survey_mdd"` string). Being considered: a
  reference marker (e.g. `@survey_mdd`) or an explicit JSON form such as
  `{ isReference: true, name: "survey_mdd" }`. Not implemented — needs a decision.
- **`/functionality/run-rule` has no folder context**, so an isolated rule passed
  as JSON cannot resolve folder aliases (only the `load_cases` / run-QC-tests path
  resolves them). Needs a rethink — e.g. accept a scope/aliases map in the request
  or route it through `load_cases`. Recorded as a real open question.
- Planned (not implemented): **conditional markers** for `meta.markers` — skip a
  rule only on certain platforms/tools (e.g. Windows-only rules for `pywin32`),
  driven by an env var set by the outer `run_*.sh`/`.bat` script (real
  expressions can't run in markers; the outer script computes the value and the
  marker just checks it). Placeholder only — see `docs/development.md` and
  `.clinerules/05-domain-model.md`.
- `named collection` is provisional — see `docs/cmdlet-data-formats.md`; decide
  whether to drop it or promote it once source readers and the full cmdlet set
  are implemented.
- End-to-end datetime-range filtering is still not wired in the QC rules list
  (`created_at`/`modified_at` remain `text` columns). The canonical value type is
  decided (`Date` objects) and the range inputs/matchers now comply, so wiring
  `date`/`datetime` columns should just mean building record fields as `Date`
  objects in `qcrules_list/toRecord`.
- Full *runtime* cmdlet value objects (categoricals, and the block / named
  collection / array wrappers) are still **not implemented**; the value-type
  *taxonomy* (`src/cmdlets/value_types.py`) now exists for annotations, and the
  plain-Python rules in `docs/cmdlet-data-formats.md` still apply (`None` for
  `sysmissing`, `dict` for block, `list` for array). Remaining to build: the
  runtime value objects, the full middle/terminal cmdlet set (`select-property`,
  `select-properties`, `select-item`, `where`, `map`, `to-string`, …), and
  further source readers.
  Built-ins are `literal`, `count`, `sort`; `get-content-excel` is a first
  (optional-dependency) source reader and `validate-xml-compatible` a first
  (optional-dependency, `validate-` prefixed) terminal validation cmdlet — see
  `docs/development.md` "Optional dependencies".
- SQLite is the "default" only by convention (docs/examples); there is no fallback.
  Decide whether SQLite should auto-create a missing file instead of requiring it
  to exist (currently it matches YAML's fail-early behavior).
- `.db` extension is intentionally **not** mapped to SQLite (ambiguous); add it
  only if a concrete need appears.
- The QC-rules page can now **create a rule via a modal form** (one input per
  field, always at the top level), **create a group**, and **add a folder alias**
  (the latter two still via `window.prompt`, hitting `/qc/groups`). Full
  rule/group CRUD UI is still not implemented: edit, delete, rename, move rules
  between groups, and the Edit/Run action buttons remain placeholders — the
  endpoints exist and are exercised by `tests/test_endpoints_rule_crud.py` and
  `tests/test_endpoints_group_crud.py`, but there is no UI yet to move an
  existing rule into/out of a group.


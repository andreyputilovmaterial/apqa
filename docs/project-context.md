# Project context

> Living document. Updated after every task. Read this first at the start of every task.

## Last state

- **QC-rules UI: folders now show a last-run summary with pytest-style counts.** `grouping.js`'s `groupRunAggregate` changed from booleans to per-status counts (`total`, `passed`, `failed`, `errored`, `running`, `blank`) and each group node now carries `runAggregate`; `groupRunStatus` derives its status from those counts (same statuses as before). `run_result.js` gains `groupRunSummary(counts)`, rendering `N passed, M failed, K error, R running, B not run` with zero counts omitted. `rules_tree.js` renders a new `.apqa-rules-tree-group-run-result` banner between the folder action row and the meta row, reusing the rule banner's status classes for color (green passed / red failed / grey otherwise); it stays hidden until at least one rule inside has a result (blank or empty folders show nothing); the summary line itself is regular weight (`font-weight: 400`, a dedicated `.apqa-rules-tree-group-run-result-status` class), not the rule status's bold weight. The folder tick still re-aggregates the same way. Tests: new `groupRunSummary` cases in `run_result.spec.js`, an aggregate-counts case in `grouping.spec.js`, and folder-summary render/hide cases in `rules_tree.spec.js`; frontend Vitest 312 passed.

- **QC-rules UI: folder "Run" now executes every rule in the folder in sequence.** `index.js`'s `onRunGroup` no longer shows the placeholder alert: it collects the folder's rules with a new `rulesForGroup(groups, records, groupId)` helper in `grouping.js` (depth-first, nested sub-folders included, in the same order the tree renders) and awaits each one through the extracted `runRuleRecord` (the former single-rule body of `onRunRule`, now shared by both paths). Each rule still POSTs `/functionality/run-rule` and writes its cached result into `runResults`, so the folder tick re-aggregates from `running` → passed/failed automatically; the folder run does not make a new backend endpoint. An empty folder shows a "This folder contains no QC rules to run." alert. Tests: new `grouping.spec.js` `rulesForGroup` cases and a new `index.spec.js` case asserting the rules run in order `['r1','r2']`; frontend Vitest 304 passed.

- **QC-rules UI: inline edit forms now mirror the display header, and folders got an inline edit form.** The rule edit form (`rule_edit_form.js`) no longer replaces the card with a bare field list: it reuses the same `.apqa-qcrules-entry`/`.apqa-rule-card` box and renders the same name+comment header, then an icon action row with Save (`ri-save-3-line`, green on hover) and Close (`ri-close-circle-line`, red on hover — added `.apqa-record-action-cancel:hover` in `styles.css`), then the unchanged field sections (collapsed read-only id, name, comment, left/op/right, tags, markers), then full-size bottom buttons "Close"+"Save" (was "Cancel"). Reusing the box class (not re-adding padding overrides, which would fight `.apqa-qcrules-entry`) keeps the header position stable when switching to edit mode. A new inline `GroupEditForm` (`group_edit_form.js`/`.css`) edits folder name/comment/tags/markers with the same header + icon-row + bottom-buttons layout; it is wired through `rules_tree.js` via a new `editingGroupId` prop and `save-group`/`cancel-group` events, and `index.js` gains `onSaveGroup`/`onCancelGroupEdit`. Folder save PUTs only `name`+merged `meta` (backend `update_group` merges, so `parent`/`aliases`/`order` are preserved) and looks up the original group record by id from `groups.value`. `tagSuggestions` now includes folder tags. Guards: `onEditRule`/`onEditGroup` block starting a rule/folder edit while the other kind (or another folder) is being edited; the tree refuses to collapse/paginate while any edit is open, and the drag-surface handler now skips `.apqa-rule-edit-form, .apqa-group-edit-form` headers so editing labels don't start a reorder. Tests: new `group_edit_form.spec.js`, plus new cases in `rule_edit_form.spec.js`, `rule_record.spec.js`, `rules_tree.spec.js` (folder edit render/save/cancel + no-drag-from-edit-header), and `index.spec.js` (folder save payload + folder tag suggestions); frontend Vitest 299 passed.

- **QC-rules UI: rule/folder descriptions now render on a separate line under the name.** The rule card head (`.apqa-rule-card-head` in `qcrules_list/styles.css`) changed from a wrapping row to a column (`flex-direction: column; align-items: flex-start`), so `name`, `comment` and any `unfinished`/`invalid` note each sit on their own line; the `—` `::before` separator on `.apqa-rule-card-comment` and the now-unneeded `flex-basis: 100%` note-forcing rule were removed. Folders got the same treatment: `rules_tree.js` moved the `.apqa-rules-tree-group-comment` span out of the toggle+name `.apqa-rules-tree-group-header-row` into the header as a sibling, and its CSS dropped the `—` separator plus the single-line `white-space: nowrap`/ellipsis truncation so it can wrap on its own line. Frontend Vitest 287 passed; updated the `rules_tree.spec.js` test name to match.


- **Restructured QC-rules list cards (rules + folders) into five always-visible sections; removed the per-rule expand/collapse view.** `rule_body.js` is now the single always-shown rule card (`rule.js`/`rule_compact.js` deleted): (1) name/comment header (`.apqa-rule-card-head`, also the reorder drag surface), (2) an icon-only action row (Edit `ri-edit-box-line`, Run `ri-play-large-line`, Delete `ri-delete-bin-6-line` — dark grey `#555` fading to primary green `var(--mdm-color-primary)` on hover, borderless, pointer cursor), (3) the cached last-run result (unchanged `.apqa-rule-run-result-*` colors), (4) the rule content (left/op/right compact cmdlet chips), (5) meta (tags + mark badges + created timestamp). `rule_record.js` lost `expanded`/`toggle` and the `ri-arrow-*-double-fill` glyph; clicking the rule header no longer toggles anything. `rules_tree.js` restructured the folder node: the header is now a `role="button"` `<div>` (keeps the `[+]`/`[-]` toggle and stays the drag surface via `.apqa-rules-tree-group-header`), and the same icon action row + a meta row sit beside it as siblings of the toggle (no nested buttons), so those buttons never start a drag. Folders now also surface `meta.tags`/`meta.markers` (extracted in `index.js` `toGroupRecord`, carried onto group nodes in `grouping.js`; the backend already stores them in `Group.meta` — no backend/db change). New `rules_tree` events `edit-group`/`run-group`/`delete-group`: edit and run are placeholders (`window.alert` for now — folder edit dialog and folder-sequential run are follow-ups), delete POSTs `DELETE /qc/groups/<id>` through a generalized `RuleDeleteConfirm` (`kind` prop). Tests: new `rule_body.spec.js`, rewrote `rule_record.spec.js`/`rules_tree.spec.js`/`index.spec.js` for the no-toggle card plus folder action/meta cases; frontend Vitest 283 passed. Follow-up: the delete action's icon now fades to red (`var(--mdm-color-error)`) on hover instead of the primary green. Follow-up: an expanded folder with no rules/sub-folders now shows a muted "Nothing to show" placeholder at the child indent, below its aliases if any (`.apqa-rules-tree-group-empty`; `hasChildren` added to group nodes).


- **Added `get-filesystem-obj-info` source reader** (`src/cmdlets/get_filesystem_obj_info/`). Stats a filesystem object into a block `{type, size, mtime, ctime, birthtime}`: `type` is `file`/`directory`/`other` (via `stat.S_ISREG`/`stat.S_ISDIR`), `size` is `st_size`, and `mtime`/`ctime`/`birthtime` map one-to-one onto `os.stat_result` as timezone-aware UTC datetimes — `birthtime` is `sysmissing` when the platform has no `st_birthtime` (checked with `getattr(st, 'st_birthtime', None)`), deliberately *not* glossing whether `st_ctime` is "creation" or "change" time. Returns `sysmissing` when the path does not exist (catches `FileNotFoundError`). Declared `kind='source'`, `permissions=['filesystem']`, compact spec `[file] path` — same `[file]` logo as `get-content-text` on purpose (it returns file *metadata*, not content). Stdlib only (comment-only `requirements.txt`). Registered in `src/cmdlets/__init__.py`; tests in `tests/test_get_filesystem_obj_info.py`; metadata assertions in `tests/test_cmdlet_metadata.py`; docs in `cmdlet-data-formats.md`. Full backend suite: 968 passed.

- **Added an in-memory `UserSettings` placeholder and wired cmdlet permission-group enforcement.** `src/user_settings.py` defines `UserSettings` (a `group -> bool` permission mapping where absent groups are granted by default, so a fresh instance grants everything) plus a `ContextVar` scope (`user_settings_scope` / `current_user_settings`). `src/main_ui_program.py` now creates one instance per session and stores it as `config['user_settings']`, and its `iface` `run_rule` / `run_rule_with_report` closures bind that settings object. `src/cmdlets/chain_runner.py` checks each cmdlet's declared `permissions` before running it and raises `PermissionDeniedError` (wrapped in `ChainError`) when a required group is not granted; nested chains (`map` transform, `where` predicate, operand chains) inherit the same settings via the `ContextVar`. `run_rule` / `run_rule_with_report` gained an optional `settings` param (default `None` = grant all). Docs updated in `cmdlet-data-formats.md`, `development.md`, and the registry docstrings; new tests in `tests/test_user_settings.py`. Full backend suite: 960 passed.

- **Logical/bitwise cmdlets got compact short forms (`AND( … )`, `OR( … )`, `BITAND( … )`, …), with baseline-aligned, spaced text.** The operand-combining cmdlets — `logical-and`, `logical-or`, `logical-tristate-and`, `logical-tristate-or`, `bitwise-and`, `bitwise-or`, `bitwise-xor`, `bitwise-lshift`, `bitwise-rshift` — each declare `compact: [{'text': '<KEYWORD>('}, {'arg': 'operands', 'role': 'operands'}, {'text': ')'}]`; the `operands` role supplies the space, because literal spaces in spec text don't render. `logical-and`/`logical-tristate-and` share `AND` (same for `OR`); bitwise keywords are `BITAND` / `BITOR` / `BITXOR` / `BITLSHIFT` / `BITRSHIFT`. Frontend: `cmdlet_chains/compact.js` renders each nested chain via `component-cmdlet-chain-compact` separated by `, ` (was the JSON placeholder), and `cmdlet/shared.js` passes `cmdlets` down to `cmdlet-chains` arg parts (`valueComponentProps`). **Whitespace + baseline follow-up (diagnosed live on an `AND(false, true)` rule):** the keyword/paren text and operand text were ~7px apart (parts were `vertical-align: bottom` while nested chips top-aligned) and the literal spaces weren't rendered at all. Fixed by changing `.apqa-cmdlet-part` to `vertical-align: baseline`, making `.apqa-cmdlet-role-operands` `display: inline` with `margin: 0 0.6em`, and unboxing nested operand chips (`.apqa-cmdlet-role-operands .apqa-cmdlet { vertical-align: baseline; border: none; padding: 0 }`) — removing the chip border/padding removes the 4px overhang that otherwise pushed the whole `AND(…)` chip's baseline below its neighbouring left-chain/cmp-op chips, so `AND(` / operands / `)` and the neighbours now share one baseline. Unary/array processors (`logical-not`/`logical-any`/`logical-all`, the `*-tristate-*` `not`/`any`/`all` variants, `bitwise-not`) are untouched (they take no operands). Tests: `test_cmdlet_metadata.py::test_logical_bitwise_short_forms`, new `cmdlet_chains/compact.spec.js`, an end-to-end `rule_compact.spec.js` case. Validated: Python pytest 950 passed / 2 skipped / 11 xfailed, frontend Vitest 282 passed / 33 files, plus live browser measurements (all text tops equal, 8px gap each side of the operands, natural wrap keeps `AND(` with the first operand and `)` with the last).


- **Drag-and-drop reordering now starts from the rule/folder header — the drag handle marker was removed.** The `.apqa-rules-tree-handle` button (remixicon `ri-drag-move-2-line`) is gone from the left gutter, which now holds only the per-rule run tick. A press on a rule/folder header (`.apqa-rule-compact-description` / `.apqa-qcrules-list-item-head` / `.apqa-rules-tree-group-header`) starts a candidate drag via a delegated `pointerdown.capture` on the tree root; a delegated `click.capture` swallows the click that follows a drag so a drag never toggles the row. **Desktop (mouse/pen) starts dragging as soon as the pointer moves ~8px**; **touch requires a ~400ms press-and-hold** (10px slop), so a quick swipe keeps scrolling the page and a tap still toggles — headers carry `touch-action: pan-y`, and once the hold fires a non-passive `touchmove` handler `preventDefault()`s to stop scrolling while dragging. Drop semantics unchanged: top quarter of a row = move **before** it, bottom quarter = **after** it, middle of a **folder** = **inside** it (a rule's middle splits to before/after); gaps/above-all/below-all resolve to before/after the nearest row. `rules_tree.js` owns the gesture state (`drag = {draggingKey, targetKey, position, suppressClick}` plus a plain `pointer` pending state) and hit-tests rendered `<li data-node-key>` elements via `getBoundingClientRect`; a valid drop emits `reorder`, which `index.js` POSTs to `/qc/reorder` and reloads.
  - **Backend:** new `POST /qc/reorder` endpoint (`src/frontend/endpoints_reorder.py`, registered in both `endpoints.py` files) with body `{kind: 'rule'|'group', id, parent, before}` — `before` is a prefixed sibling key `r:<id>`/`g:<id>` (unambiguous across the separate rule/group id spaces), null = append. The shared `DBFile.reorder` (in `dbfile_base.py`, works for YAML + SQLite) resolves the parent, rejects folder cycles (`_validate_group_parent`), combines sub-folders + rules into one ordered sibling list (matching the UI tie-break: folders before rules, insertion order), inserts the moved item, renumbers the target parent's children to consecutive `meta.order` integers, and persists via existing `update_rule`/`update_group`.
  - **Frontend:** `rule_record.js` lost the handle button, the `handle-down` emit, and its `onHandleDown`; it keeps `nodeKey`/`draggingKey`/`dropTargetKey`/`dropPosition` for the `.apqa-is-dragging` / `.apqa-is-drop-*` feedback classes. `rules_tree.js` gained `onHeaderPointerDown`/`onClickCapture` and the touch hold timer (the pure `reorder.js` descriptor math is unchanged). `styles.css` dropped `.apqa-rules-tree-handle`, simplified `.apqa-rules-tree-gutter` to `min-width: 21px`, and added `gap: 10px` on `.apqa-rules-tree-item` (run tick → rule/folder content). The group-reload `watch` no longer re-folds every folder — it now folds only newly added folders (tracked via a `knownGroupIds` Set) and prunes removed ones. **The actual re-folding culprit was `index.js`'s `load()` setting `loading.value = true` on every reload** — the template gates the whole tree behind `v-if="loading"`/`v-else`, so each reload unmounted and remounted the tree, resetting all folder/rule state. `load()` no longer re-sets `loading` (it is initialized to true and only cleared), so reloads after create/delete/save/reorder update the data in place.
  - Tests: replaced the handle tests with header-drag cases — `rules_tree.spec.js` now asserts a folder-header drag and a rule-header drag both emit `reorder`, that a plain header click still expands, and that a drag swallows the following click; plus cases that a group reload with the same ids keeps folders expanded (reorder), a newly added folder starts folded, and a rule stays expanded when its record reloads (keys by `node.key`). `index.spec.js` gained an end-to-end case that a reorder reload keeps a folder expanded (i.e. the tree is not remounted). The handle-emit case in `rule_record.spec.js` was removed. Validated: frontend Vitest 279 passed / 32 files, `build.sh` OK (bundle contains `touch-action: pan-y` and `gap: 10px`, no `apqa-rules-tree-handle`/`handle-down`). **The touch long-press path is not live-tested on a real device** (jsdom can't simulate touch; the dev backend on 5280 points at sensitive real data so it was left untouched) — it follows the MDN recipe (long-press + `touch-action: pan-y` + non-passive `touchmove` `preventDefault()`), but should be sanity-checked on an actual phone/tablet.

- **Implemented the "Create folder" flow and folder description/comment.** The toolbar button was renamed from "Create group" to "Create folder" and now opens a modal form (new `group_form.js` + `group_form.css`) with folder name + comment/description instead of the old `window.prompt`-based flow. On submit it POSTs `/qc/groups` with `{name, parent: '', meta: {comment, order}}` — always top level, appended after the largest existing order (rules and folders share one order space, mirroring rule creation). Folders now surface their description like rules do: `toGroupRecord` maps `meta.comment` → `comment`, `buildGroupNodes` carries it onto group nodes, and `rules_tree.js` renders a muted `.apqa-rules-tree-group-comment` next to the folder name (styles.css). The backend already stored folder `meta` (hence `meta.comment`); confirmed end-to-end with a new `test_create_group_with_comment` endpoint test. Removed the now-unused `groupIdFor` helper. Tests: `group_form.spec.js` (3), `grouping.spec.js` comment-on-node, `rules_tree.spec.js` folder-comment render, backend `tests/test_endpoints_group_crud.py`. Validated: frontend Vitest 260 passed / 31 files, Python pytest 937 passed / 2 skipped / 11 xfailed, `build.sh` OK (bundle contains the new form/styles).


- **Added a spinning run-state loader and folder-level combined run ticks.** `onRunRule` already set a transient `running` status before fetching; the rule tick now shows a spinning `ri-loader-4-line` (`.is-running` + `apqa-run-tick-spin` keyframes) during that window instead of an empty box. Folders now carry their own tick in the gutter, computed in `buildGroupNodes` via a recursive `groupRunAggregate` (memoized, cycle-guarded) + `groupRunStatus`: `failed`/`error` dominates, then `running`, then `passed` only when every descendant rule passed, then `indeterminate` (`±` via `.apqa-run-tick-text`) when some rules passed and some are still blank, `blank` (an empty `is-empty` square) when nothing inside has run, and `empty` (no rules inside) shows no tick. The status→indicator mapping is a shared `runTickFor` in `run_result.js`, used by both `rule_record.js` (rules) and `rules_tree.js` (folders). Tests: `grouping.spec.js` run-status cases, `rule_record.spec.js` running case, `rules_tree.spec.js` folder-tick cases. Validated: frontend Vitest 255 passed / 30 files, `build.sh` OK, and live-browser checks confirmed blank squares on fresh load and a nested rule failure turning its folder tick red.


- **Aligned the per-rule run ticks into one fixed left column and shifted the whole QC-rules tree 30px right.** Replaced the tick's absolute positioning (which drifted right with each nesting depth) with a real layout: each tree `<li>` is now a flex row of a fixed 30px `.apqa-rules-tree-gutter` cell (holding the tick) plus a `.apqa-rules-tree-content` cell that carries the depth indentation (`padding-left: calc(var(--rules-tree-depth, 0) * var(--mdm-space))`). The tick markup and its `tickIcon`/`tickClass`/`tickTitle` computeds moved from `rule_body.js` up to `rule_record.js`; folder rows get an empty gutter cell so their headings align with rules. No `position: absolute`, no negative offsets, screen-independent. Validated: frontend Vitest 239 passed / 30 files, `build.sh` OK, and live-browser measurements show every tick at the same x (left 45) for depth 0 and depth 1 rules while depth-1 cards stay indented (left 105 vs depth-0 left 75).


- **Added a per-rule pass/fail tick to the left of each QC rule in the list.** A new `.apqa-rule-run-tick` box sits in the tree's left indent gutter (`position: absolute; left: -28px; top: 0`, 21×21px, light grey `#e0e0e0` border, transparent background), driven by the same cached `runResults` map keyed by rule id: empty when not run yet, a green `ri-check-double-line` (`var(--mdm-color-confirm)`) after a passed run, and a red `ri-close-fill` (`var(--mdm-color-error)`) after a failed or errored run (a transient `running` state stays empty). Implemented in `rule_body.js` (tick span + `tickIcon`/`tickClass`/`tickTitle` computeds) with `.apqa-rule-body` made `position: relative`; no extra prop threading was needed because `runResults` was already passed down from the previous task. Tests: 4 new tick cases in `rule_record.spec.js` (empty/passed/failed/error). Validated: frontend Vitest 239 passed / 30 files, `build.sh` OK (bundle contains the tick styles + icons).


- **Implemented the QC-rule "Run" button in the frontend.** `onRunRule` in `qcrules_list/index.js` now POSTs the full rule (`name/id/group/meta/left/op/op_args/right`, mirroring `Rule.to_dict()` / `rule.run()`) to the existing `POST /functionality/run-rule` endpoint, which executes it through the same `run_rule_with_report` path as `run_tests.sh` → `tstsuite.py` → `rule.run()`. Results are cached in a page-level reactive `runResults` map keyed by rule id — kept on the page rather than on record objects because `component-records-filter` passes shallow copies down, so a result written onto a copy would be lost on recompute; the cache survives list reloads and is cleared when a rule is saved/deleted. A new banner renders above the Edit/Run/Delete buttons: green "Passed", red "Failed" (plus red diagnostic-note lines via a new `run_result.js` `formatPath`/`formatNote` mirroring `src/cmdlets/diagnostic.py`), or a red exception snippet when a cmdlet raised, with a transient grey "Running..." in flight. `runResults` is threaded `index.js` → `rules-tree` → `rule-record` → `rule-body` as a prop. New tests: `run_result.spec.js`, banner cases in `rule_record.spec.js`, run/error flows in `index.spec.js`. Validated: frontend Vitest 235 passed / 30 files, `tests/test_endpoints_rule_run.py` 9 passed, `build.sh` OK (bundle contains the new banner + endpoint call).


- **`filter` now matches full data paths written as a list of strings, and there's a new `strings` arg type with a real list editor.** `filter.ignorelist` is now `type: 'strings'` — a list of path strings in the `format_path` notation (`.key`, `[i]`, `['quoted']`) — and the cmdlet deep-traverses the received value (`_prune`), prepending the navigation prefix (`_prefix_segments` from `current_navigation()`) and deleting any node whose full path is in the list; a path naming a node removes that subtree, a path equal to the filter's own position returns `None`, and a non-matching path is ignored. The `first_kinds` plumbing was reverted (it only existed for the earlier `cmdlet-chains`-based paths). New `strings` arg editor (`common_components/input_types/cmdlets/data_types/strings` — add/remove rows, one text input per value) + compact/full display components, registered as `component-input-cmdlet-arg-strings` / `component-cmdlet-arg-strings-*`; `defaultArgValue`/`defaultForType` treat `strings` as `[]`. `navigation.py`/`chain_runner`/`select-field`/`select-item` are unchanged. Tests rewritten in `tests/test_filter.py` (string paths), metadata assertion updated, new Vitest spec for the editor. Backend 509 passed / 2 skipped, frontend Vitest 222 passed / 29 files.

- **Removed the `|` pipe separator between cmdlet chips and gave `select-field` a `->` compact form.** The read-only chain renderer (`cmdlet_components/cmdlet_chain/shared.js`) no longer inserts a `|` span between cmdlets — chips are now separated only by a 6px gap (`.apqa-cmdlet-chain .apqa-cmdlet:not(:first-child) { margin-left: 6px }`), and each cmdlet renders its own leading indicator (source logos `[mdd]`/`[xlsx]`/…, `select-field`'s new `->`). `select-field` now declares `compact: [{text: '->', role: 'arrow'}, {arg: 'field'}]` (new `arrow` role with `margin-right: 0.3em` in `cmdlet/styles.css`), so `get-content-mdd … -> fields -> SnifferData -> fields -> Cluster -> …` renders without pipes. Non-final decisions (autofocus + Enter-to-append editor flow, auto-suggestion/pinning machinery, and the rejected pre-fill-by-pre-flight idea) are recorded in `docs/roadmap.md` only, no code. Tests: `test_cmdlet_metadata.py` asserts the new spec; backend 498 passed / 2 skipped, frontend Vitest 218 passed.

- **`get-content-mdd`: block/class fields now store sub-fields under `fields` (was `value`).** `_read_block_field` (ObjectTypeValue 3) now sets `block['fields'] = self._read_subfields(field)` and `block['value'] = None`, matching how array/grid columns are already stored under `fields`. So a diagnostic data path for a block field now reads `fields.SnifferData.fields.Cluster.categories.Select.label` (was `…SnifferData.value.Cluster…`). Docstring + `docs/cmdlet-data-formats.md` updated; new test `test_block_field_stores_subfields_in_fields_bucket` in `tests/test_get_content_mdd.py`. Full backend suite: 498 passed / 2 skipped.

- **Clarified `get-content-mdd` data-path naming (Q&A, no code change).** The diagnostic note path renders the *normalized block* keys, not the COM access path, so `fields.SnifferData.value.Cluster.categories.Select.label` means: `fields` = the top-level result-block **section** (one of `source_file`/`languages`/`shared_lists`/`fields`/`pages`/`routing`); `SnifferData` = a field key; `value` = that field block's payload — for a block/class field (ObjectTypeValue 3) `value` **is** the block of subfields (`_read_block_field` → `block['value'] = self._read_subfields(field)`), which is why it's `value.Cluster`, not `fields.Cluster`. In COM both levels are uniform `.Fields` collections, but the block separates a document section (`fields`) from an item's payload (`value`).

- **Added a diagnostic-notes + chain-error layer so a failed QC rule reports *where* it happened (new spec `docs/qc-results-reporting.md`).** Two mechanisms: (1) `src/cmdlets/chain_runner.py` now wraps any cmdlet failure in a `ChainError` that names the failing step (`cmdlet 'x' (step i): …`) with the original exception chained as `__cause__` (unknown-cmdlet lookup is wrapped too; a missing comparison op is not). (2) `src/cmdlets/diagnostic.py` adds an out-of-band **notes** channel — a `contextvars.ContextVar`-scoped `Notes` list + `collect_notes()`/`record_note()`/`current_notes()` and `format_path`/`format_note`/`format_notes` — so validators record `{path, message}` notes whose `path` is the **data path** (block keys + array indices, e.g. `fields.BrandAwareness.label`, `pages.Q1.value[2]`). `rule_runner.run_rule_with_report(rule)` returns `(result, notes)`; `run_rule` delegates to it and discards notes, so `Rule.run()` still returns a plain bool. `validate-xml-compatible` now records a note per failing text leaf (message includes the parse error + clipped value); it still returns a plain bool so the `… cmp-eq literal(True)` rule keeps working. `tstsuite.run_tst_case` builds a rich `AssertionError` (`QC rule failed: <name> [<id>] (result: False)` + bulleted `format_notes`); `POST /functionality/run-rule` returns `{result, notes}` when the config exposes `run_rule_with_report` (added to `main_ui_program` iface, both import branches) and stays `{result}` otherwise. Tests: new `tests/test_diagnostic.py`; updated `test_rule_runner` (ChainError + report-notes cases), `test_tstsuite` (message includes id/name/notes), `test_endpoints_rule_run` (report config + notes), `test_optional_dependencies` (ChainError with `__cause__`). Backend suite: 497 passed / 2 skipped.


- **Polished the rule-form arg editors: uniform row layout, matched control heights, a `true`/`false` boolean drop-down, and a shared `sysmissing` "unset" opt-out for every type.** Root cause of the earlier misalignment was a CSS class collision: my `literal-value` editor's root class `.apqa-input-cmdlet-arg-literal-value` matched the arg-wrapper's auto class `.apqa-input-cmdlet-arg-<type>` (type `literal-value`), so the editor's row CSS leaked onto the wrapper and top-aligned the label. Renamed the editor's classes to `.apqa-input-literal-value-*`. `InputCmdletArg` (`cmdlet_arg/`) now renders label + control + an "unset" checkbox on one vertically-centered row (help text below), with `line-height: 1.2` on `.apqa-input-cmdlet-arg-input` and a flattened (`appearance:none`) select + inline SVG caret so selects match text-input height. `boolean` args are now a `true`/`false` drop-down (was a checkbox); the "unset" checkbox is the uniform opt-out that stores `null` for *any* type and restores the last non-null value on uncheck (muted via `is-unset`). The `literal` type selector now offers `text`/`number`/`boolean`/`path`/`date`/`json`; `date`'s editor stores blank → `null` like `path`/`number`. Docs updated (`cmdlet-data-formats.md` "Arg values", `development.md` arg-types). Validated in-browser (select/input both 27px, label centered) + frontend Vitest 218 passed / 28 files; backend 479 passed / 2 skipped.

- **Gave the `literal` cmdlet a typed value editor (`literal-value` arg type).** Before, `literal.value` was a raw `json` text input, so setting a boolean meant typing bare JSON (`true`, where `"true"` is text) — undiscoverable, the user hit this live. Now `literal.value` declares `type: 'literal-value'`; the frontend renders a type selector (`text` / `number` / `boolean` / `json`) plus the matching typed input (checkbox for boolean, number input, text input, raw-JSON escape hatch). The stored `args.value` stays a **single JSON value** — no separate type field, so existing rules keep working; the selector is a *view* over the value (inferred from its JSON type on open, coerced on change: text → stringified, number → parsed or `sysmissing`, boolean → kept or `false`, json → kept). Added: editing component `input_types/cmdlets/data_types/literal_value/` (+ `index.spec.js`), type-aware display components `cmdlet_components/data_types/literal_value/` (strings render quoted, so text `"true"` ≠ boolean `true`; + `shared.spec.js`), registration in both component registries, a `defaultArgValue` case, a backend metadata test, and doc updates (`cmdlet-data-formats.md`, `development.md`). Validated: backend 479 passed / 2 skipped; frontend Vitest 216 passed / 28 files (11 new tests).

- **Started the `print()` → `logging` migration for the app entry points (scope agreed with user).** Added `src/helper_logger.py` with `setup_logging()`: a single `apqa` logger, INFO→stdout / WARNING+→stderr, bare `%(message)s` formatter (messages carry their own colors), and a `_DynamicStreamHandler` that resolves the stream at emit time so pytest's `capsys`/redirection still sees output. `src/main_init_program.py` and `src/main_ui_program.py` now call `setup_logging()` at the top of `main()` and log their informative progress (`starting …`, `preparing webserver…`, `CONFIG:\n…`, `created …`) via `logger.info(...)`. Per the user: `src/launcher.py`'s `call_test_program`/`call_done_program`/`call_printversion_program`, `main_print_help.py`, and `src/webserver_engine/*` are **functional output and stay as `print`** (no submodule commits); stderr error reporting stays as `print(..., file=sys.stderr)`. `dev_backend.py`, `http_db_server.py`, and `minify_assets.py` are also left as-is. Validated: full backend suite 478 passed / 2 skipped; `python -m src.launcher --program init --db-file …` still prints the same lines.


- **Made `build_templates.py` build output concise with a `-v`/`--verbose` flag.** Before, `html-template build` printed a `script started at` line, one `saving as "<path>"` line per generated file (the `vendor-libs` resource emits hundreds of font/license/css files), and a `finished at` line. Now progress output goes through a new `build_templates` logger (`configure_logging()` configured at import): by default only `html-template build: building <resource>...` and `html-template build: done (elapsed ...)` are shown (INFO), while `script started at` and the per-file `saving as ...` lines are DEBUG. The new top-level `-v`/`--verbose` flag in `main()` (captured by `parse_known_args`, so it works before or after `--program`) raises the logger to DEBUG; the `transform-run-script` completion line now uses the same logger. Error messages remain on stderr. Validated: `vendor-libs` prints 2 lines by default and the full list with `-v`; `tests/test_build_templates.py` 5 passed.


- **Inlined optional cmdlet dependencies into the dist run scripts and dropped the `dist/optional_dependencies/` folder.** The Windows `run_init.bat` "file not found" errors were caused by `for /r "...\src\cmdlets" %%f in (requirements.txt)` — with a literal (non-wildcard) name, `for /r` enumerates every directory and constructs `dir\requirements.txt` even when the file does not exist, so it tried `optional_dependencies\requirements.txt` and `optional_dependencies\cmdlets\requirements.txt`. Now `build.sh` no longer copies `src/cmdlets/**/requirements.txt` into `dist/optional_dependencies/`; instead `build_templates.py --program transform-run-script` scans those files and inlines one `pip install` statement per installable specifier directly into `dist/run_init.sh` / `dist/run_init.bat` (comment-only stdlib files are skipped). The block to replace is delimited by `BEGIN OPTIONAL-DEPS`/`END OPTIONAL-DEPS` markers in the root scripts; the root `run_init.bat` dev block was also fixed to use `for /f ... dir /s /b` instead of the buggy `for /r`. `dist/` now carries a single global `requirements.txt`. Updated `docs/development.md`, `.clinerules/10-optional-dependencies.md`, the comment-only `requirements.txt` files, resolved the roadmap item, and added `tests/test_build_templates.py` (parsing + inlining + build-block strip). Validated: 478 backend tests pass; ran `transform-run-script` on all 6 run scripts and confirmed no `optional_dependencies`/`for /r`/`find src/cmdlets`/`dir /s /b` references remain and the three installable specs (`openpyxl>=3`, `pywin32`, `beautifulsoup4>=4`) are inlined.


- **Added a declarative `permissions` metadata field to cmdlet registration.** `CmdletRegistry.register(...)` now accepts `permissions=None` and records `meta['permissions']` via the new `registry.normalize_permissions` (a de-duplicated, sorted list; empty by default, single-string shorthand allowed), which flows automatically through `GET /functionality/cmdlet-metadata`. Tagged the file readers `get-content`, `get-content-text`, `get-content-excel`, `get-content-mdd` with `['filesystem']` and `get-content-network-fetch` with `['network']`; every other cmdlet (including `validate-network-request-result`, which only inspects an already-fetched block and makes no request itself) has `[]`. This is the declarative groundwork for the future permission allow-list — run-time enforcement is not wired yet. Updated `docs/cmdlet-data-formats.md` "Editor metadata", `docs/development.md` "Cmdlet & comparison-op editor metadata", and the roadmap security item. Added `tests/test_cmdlet_metadata.py` tests `test_every_cmdlet_has_permission_list`, `test_cmdlet_permission_groups`, `test_normalize_permissions`. Validated: 149 backend tests pass (metadata + cmdlets/standard/network).


- **Reorganized the create/edit QC rule forms into three unlabeled sections and made the technical id a collapsible "QC rule ID" line.** `rule_form.js` (create modal) and `rule_edit_form.js` (inline) now group fields under three plain `.apqa-rule-form-section` blocks separated by only a slightly larger gap (18px between sections vs 10px between fields) — no borders, titles, or indents: (1) QC rule ID + Name + Comment, (2) Left side + Comparison + Right side, (3) Tags + Markers. The technical id now always sits above the name (the edit form previously had name first). It renders collapsed as a one-line dark-grey value (`#555`, base 14px) preceded by a `.ri-arrow-down-double-fill` icon; clicking that line (cursor pointer) toggles the icon to `.ri-arrow-up-double-fill` and expands the same input as before (editable in create, read-only in edit). The create form's collapsed value auto-updates live from the name via the existing `makeUniqueSlug` watcher. Wording changed from `Technical name (id)` → `QC rule ID`; the edit help text now reads "The QC rule ID cannot be changed." CSS lives in `rule_form.css`; specs updated (`rule_form.spec.js`, `rule_edit_form.spec.js`) with 2 new tests covering the collapse/expand + ordering. Validated: 205 vitest tests pass; verified live through the Vite dev server (backend on :5280).


- **Introduced a derived `invalid` mark for QC rules referencing an unrecognized cmdlet or comparison-op name** (or a cmdlet step that is not a `{cmdlet, args}` object), frontend-only in `qcrules_list/grouping.js` alongside the existing `unfinished` mark. `unfinished` = a piece is missing; `invalid` = a piece is present but uninterpretable in this environment (it fails at run time). Cmdlet detection recurses into nested `cmdlet-chain`/`cmdlet-chains` args; op detection compares `record.op` against the loaded `ops` metadata. Like the missing-required-arg check, both are disabled while metadata has not loaded (`cmdlets`/`ops` empty) so an unloaded list never paints every rule `invalid`. The mark renders as a badge with a `title` tooltip (`INVALID_MESSAGE` in `marks_badges.js`), a grey helper note under the rule's name (`rule.js`/`rule_compact.js`), and a pale-red entry highlight slightly pinker than `unfinished` (`#ffe7ee` background / `#c2416b` left accent). Provisional cascade precedence is `invalid` > `unfinished` > `skip` > `xfail`. Updated `docs/development.md` "Markers", resolved `docs/roadmap.md` "highlight unrecognized cmdlets differently", and the `grouping`/`marks_badges`/`rule_compact`/`rule_record` specs. Validated: 203 vitest tests pass.\n
- **Added `logical-tristate-*` cmdlets mirroring the five `logical-*` cmdlets with SQL three-valued (Kleene) logic.** `logical-tristate-not` (`not sysmissing` → `sysmissing`), `logical-tristate-and`/`logical-tristate-or` (source readers over `args['operands']` cmdlet chains), and `logical-tristate-any`/`logical-tristate-all` (processors reducing an array). Semantics: `sysmissing` is *unknown* (neither true nor false), `false` dominates AND and `true` dominates OR, and the result may itself be `sysmissing`. Non-`sysmissing` operands/iterations are coerced with `bool()`, exactly like the plain `logical-*` family; empty arrays keep Python's `any`/`all` identities (`[]` → `false` for any, `true` for all). Shared truth-table helpers live in `src/cmdlets/tristate.py`; new folders `logical_tristate_{not,and,or,any,all}` are registered in `src/cmdlets/__init__.py`. Documented in `docs/cmdlet-data-formats.md` and tested in `tests/test_standard_cmdlets.py`. Validated: 897 backend tests pass.


- **Reviewed & fixed the `src/cmdlets` "condensed name" updates (compact display specs).** Confirmed `get-content-excel` no longer takes a `sheet` arg and returns a block keyed by every sheet name (a rule must address a sheet by name), and removed the now-resolved roadmap item. Fixed the remaining inconsistencies the edits had left behind: `get-content-mdd`'s runtime still read the pre-rename arg names (`method`/`contexts`/`step_into`) while the metadata declared `open_method`/`context`/`categories_step_into` — now aligned, `context` is a **single string** (default `"Analysis"`), labels/translations are read in that context (the reader pins `document.Contexts.Current` to it for the whole read, resolving the context object by name first), and properties iterate **all** document contexts and merge them (no `context` needed); also fixed the mis-indented `_MDDReader` class docstring. `get-content-network-fetch`'s compact spec had a bogus `{'arg': 'path'}` (that cmdlet has no `path` arg — the URL comes from the piped value), now just the `[network]` logo. Frontend: the `role=separator` part is gone from every spec, so the dead `.apqa-cmdlet-role-separator` CSS was removed and `.apqa-cmdlet-role-logo` gained `margin-right: 0.3em` (~4px at the 14px base) — measured ≈ the `:` glyph width (4.09px) and clearly less than a capital `S` (8.14px). Updated `tests/test_cmdlet_metadata.py`, `rule_compact.spec.js`, and `docs/cmdlet-data-formats.md` to drop the `separator` example. Validated: 891 backend tests pass, 188 vitest tests pass, and the 4 edited cmdlet modules compile.

- **Cleaned `docs/roadmap.md`** — removed all 12 todo items marked `(fully resolved)` (each carried a `(Done: …)` note), leaving the still-open tasks intact. Docs-only housekeeping, no code change.

- **Committed & pushed a `.gitignore` update** — added a `.roadmap-*` pattern so ad-hoc planning notes (e.g. `.roadmap-reorder-arguments.md`) stay out of the repository. Trivial housekeeping, no code change.

- **Added a third DB-file backend — HTTP/HTTPS — plus a standalone local fixture server, proving the storage abstraction is scalable.** New `src/db_processors/http.py` (`DBFileHttp`, registered under `http` and `https`) addresses a remote database by URL and speaks a single-document wire protocol (`GET`/`PUT` the whole `{project, groups, rules}` document; `404` = empty; connection/auth errors fail early). The in-memory document CRUD shared by YAML and HTTP was extracted into `src/db_processors/document_base.py` (`DBFileDocument`); `DBFileYaml` is now a thin file-transport subclass. `detect_type` recognizes `http://`/`https://`. Credentials embedded as `http://user:pass@host:port` are parsed into an `Authorization: Basic ...` header and stripped from `resource_path`, so `config['db_file']`, the page header, and `GET /qc/project` serve only the clean URL (never a resolved physical path). A stdlib-only dev fixture server `http_db_server.py` (repo root) serves the same protocol (`--seed`, `--save-to`, optional `--username`/`--password`); tests run the client against it to exercise the contract across two implementations. 891 backend tests pass.

- **Added load-time name migration for the cmdlet/op rename (fixes "`eq` shown as `eq`").** The rename left existing DB files carrying the pre-rename names, so a stored rule with `op: eq` no longer matched the `cmp-eq` metadata and the compact chip fell back to the raw name `eq` instead of `=`. New `src/db_processors/name_migrations.py` maps old → current names (`eq`→`cmp-eq`, `ne`→`cmp-ne`, `eq-unordered`→`cmp-eq-unordered`, `lt`/`le`/`gt`/`ge`→`cmp-*`, `contains`→`cmp-contains`; `and`/`or`/`all`/`any`/`not`→`logical-*`, `bit-and`/…→`bitwise-*`). `Rule.from_dict` and `Group.from_dict` now apply these maps, so a DB file read upgrades its op names, cmdlet names in `left`/`right` chains (including nested `cmdlet-chain`/`cmdlet-chains` args like `operands`/`transform`/`predicate`), and group alias chains — in memory, non-destructively (the file is rewritten only on the next save). The CRUD/storage tests that used the now-invalid old op names were updated to the new names. 451 backend tests pass.


- **Renamed logical & bitwise cmdlets and split comparison ops into per-op `cmp-*` modules.** Logical boolean cmdlets are now `logical-and`/`logical-or`/`logical-all`/`logical-any`/`logical-not` (folders `logical_*`, was `and`/`or`/`all`/`any`/`not`); bitwise cmdlets are now `bitwise-and`/`bitwise-or`/`bitwise-xor`/`bitwise-not`/`bitwise-lshift`/`bitwise-rshift` (folders `bitwise_*`, was `bit-*`) — longer names so they no longer read as common single words. Comparison ops left the single `src/cmdlets/comparison_ops.py` (deleted) and now live **one folder per op at the same level as the other cmdlets**, prefixed `cmp-`: `cmp-eq`, `cmp-ne`, `cmp-eq-unordered`, `cmp-lt`, `cmp-le`, `cmp-gt`, `cmp-ge`, `cmp-contains` (folders `cmp_*`). The `ComparisonRegistry` + `comparisons` instance moved into `src/cmdlets/registry.py`; the shared type predicates / `to_number` / `ordered_compare` helpers moved into `src/cmdlets/comparison_helpers.py`; `src/cmdlets/__init__.py` now imports each `cmp_*` module (resolving the earlier "location undecided" follow-up). `rule_runner.py`/`meta.py` still resolve ops via `comparisons` unchanged. Tests and `docs/cmdlet-data-formats.md`/`development.md`/`roadmap.md` updated; **444 backend tests pass**. Note: DB-storage/CRUD tests that only round-trip an opaque `op` string were left as-is (`eq` there is an unvalidated opaque value, not a runtime op lookup).


- **Added `compact`/`full` display specs to cmdlet + comparison-op metadata (structured parts with roles).** The read-only rule list (compact vs full views) no longer has any per-cmdlet/per-op formatting hardcoded in the frontend. Backend: `src/cmdlets/registry.py` gains `normalize_display(parts)` and `@cmdlets.register(..., compact=..., full=...)`; `comparison_ops.py` gains the same on `@comparisons.register(...)`. A spec is an ordered list of parts — a string / `{text, role}` literal or `{arg: <name>}` arg reference; roles are semantic (`logo`, `separator`, `symbol`, …), mapped to `.apqa-cmdlet-role-<role>` CSS on the frontend (never raw HTML). `get-content-excel` declares `compact` = `[xlsx]: path`; `literal` declares `compact`/`full` = its value only; `eq`/`ne`/`lt`/`le`/`gt`/`ge` declare `compact` = `=`/`≠`/`<`/`≤`/`>`/`≥`. Frontend: `cmdlet/shared.js` `makeCmdlet(form)` renders `meta[form]` spec parts (arg parts reuse the per-type value components); `comparison_op/shared.js` is now `makeComparisonOp(form)` + `opSpec()`, deleting `OP_SYMBOLS`/`comparisonSymbol` and the whole `cmdlet_renderers.js` registry (the `literal` override moved to metadata). `rule_compact.js`/`rule.js` pass `ops` to the op chip; `alias_record.js` now receives `cmdlets`. 444 backend + 188 frontend tests pass; the self-written bundler still bundles (296k chars). **Decision/follow-up:** comparison ops were *not* moved out of `comparison_ops.py` into per-op modules/folders (location undecided — same level as cmdlets vs a subfolder); only the display-spec format is now uniform between cmdlets and ops.

- **Reorganized the frontend `common_components` into grouped folders and split cmdlet rendering into object-oriented, globally-registered components (display + editing).** The flat `common_components/` now groups reusable input widgets under `input_types/` (was `input_numeric_range`/`input_datetime_range`/`input_multipunch`/`input_regex_text`/`input_search_select`, now without the `input_` folder prefix but with unchanged global tag names), the `format_*` formatters under `display/`, and the cmdlet editing components under `input_types/cmdlets/` (`cmdlet`, `cmdlet_chain`, `comparison_op`, `cmdlet_arg`, `data_types/<type>` per-arg editors — decomposed from the monolith `input_cmdlet`/`input_comparison_op`). The read-only cmdlet display lives in a new `cmdlet_components/` with two forms per entity, `X.compact.js` + `X.full.js` (compact = today's chip; `full` is a placeholder that currently renders the same chip), plus `cmdlet_renderers.js` (relocated `registerCmdletRenderer` + the `literal` override) and `data_types/<type>` per-type value renderers (incl. a dormant `date` — no backend `date` arg type exists yet). Both families register every component globally via `registerCmdletComponents`/`registerInputCmdletComponents` (`app.js`), and **within each family siblings reference each other only by global tag** (no imports) to break the `cmdlet → cmdlet_arg → data_types/cmdlet_chain → cmdlet_chain → cmdlet` cycle. Consumers (`rule_compact.js` → compact tags, `rule.js` → full tags, `alias_record.js` → compact, `rule_form.js`/`rule_edit_form.js` → editing tags) dropped their local `components` maps; the old `qcrules_list/cmdlet.js`/`cmdlet_chain.js`/`comparison.js` were deleted, and their chip CSS moved into the new component `styles.css` files. 185 vitest tests pass; the self-written bundler still bundles the app (295k chars). Note: `comparison_op` reuses `component-input-cmdlet-arg` for its `op_args` (the old `.apqa-input-comparison-op-arg*` styles are gone). Follow-up: `input_qcrule_tags`/`input_qcrule_marks` moved to `input_types/qcrules/` (`tags`/`marks`); `input_gallery` (a test-page demo, not a reusable component) moved to `app/testpage/`; `_log_error_proxy` renamed to `log_error` (its `_logErrorProxyContext` hook → `logErrorContext`); and `formatters` was renamed to `display`, with `loader_spinner`/`loader_inprogress` moved into it.

- **Removed the unused `common_components/pages` "page stack" component (a leftover from an older design).** It was dead code — its default export `PagesSite` and the `mdm-ui-pages` / `mdm-git-ui-page` markup were never imported anywhere (a whole-tree grep found references only inside the component itself). The app stays a single-screen Vue app: `app.js` mounts one fixed template, and secondary views (project settings, test page) are opened as overlays through `common_components/modals` (`ModalsSite` + `createModal`) via `background_navlinks_attachmodals/manipulate_links.js` — no router, no address-bar navigation. Decision recorded: **no vue-router**; the modal/overlay model *is* the navigation mechanism, and a router is only worth reconsidering if a genuinely URL-addressable second screen ever appears. Also dropped the now-stale "pages" word from the `// all "system" components ...` comment in `app.js`.


- **Escaped an HTML-like angle-bracket placeholder in the docs.** `docs/roadmap.md` had `the page title becomes "QC rules for <project name>"` written as plain prose, so `<project name>` could be misparsed as an HTML tag; it now reads `&lt;project name&gt;`. Reviewed every repo markdown doc (`docs/`, `README.md`, `help.md`, `.clinerules/`): all other `<...>` occurrences are already inside backticks (code spans) or fenced code blocks, so they render as literal text and are safe.

- **Cmdlets and the comparison op are now bordered "chips" (qcrules_list).**
  `.apqa-cmdlet` was a plain inline `<span>`, so vertical `padding`/`border`
  painted over neighbouring lines and vertical `margin` was ignored — the
  source of the glyph clipping and the uneven row spacing the author hit while
  experimenting with `line-height`. It is now `display: inline-block` with
  `padding: 3px 8px`, `border: 1px solid #999`, `border-radius: 7px`,
  `box-decoration-break: slice` (stated explicitly though it's the default),
  `vertical-align: top` + `margin-bottom: 3px` — `top` (not `middle`/`baseline`)
  makes the gap between wrapped chips an exact, height-independent 3px (verified
  in-browser). The pipe separator got `vertical-align: middle` so it centers
  against the chip boxes. `max-width: 100%` on the chip (plus the existing
  `.apqa-cmdlet-part` ellipsis) keeps an overlong part (e.g. a long `path=`)
  ellipsized instead of overflowing. The comparison op now renders
  `class="apqa-cmdlet apqa-comparison"` so it shares the base chip box while
  `.apqa-comparison` stays the separate hook (weight, monospace font,
  alignment). Nested-cmdlet args (whole chains as argument values, e.g.
  `and`/`or`/`bit-*` `operands`) still render as one non-breakable JSON blob and
  ellipsize rather than wrap — recorded as a UI follow-up in docs/roadmap.md.
  Follow-up: `.apqa-rule-compact-definition` now uses `align-items: flex-start` (was `baseline`, which floated the cmp-op chip ~4px above the left chain) and `row-gap: 0` + `column-gap: 8px` (was `gap: 8px`), so the cmp op sits on the same visual line as the left-chain cmdlets and wrapped rows are spaced by the chips' own 3px margin (was 8px gap + 3px margin = 11px). Verified in-browser: cmp-op top == left-chip top (diff 0), inter-row gap 3px. 185 vitest tests pass.

- **Broadened "unfinished" detection to "any missing piece" and made it
  frontend-only.** A rule is now marked unfinished when any essential piece is
  `sysmissing` (`null`): an empty left chain, an unset comparison op, an empty
  right chain, or a required argument — recursively into nested
  `cmdlet-chain`/`cmdlet-chains` args — that is missing (driven by
  `/functionality/cmdlet-metadata`). A piece that is present but unrecognized
  (unknown cmdlet name) is *not* missing. The backend skip heuristic was removed
  (`tstsuite.pytest_param_for` no longer skips "unfinished" rules; a broken rule
  fails at run time with a normal exception — a comment marks where the check
  used to be). `select-field` now accepts an empty field name (`if field is
  None` guard instead of `if not field`), and arg inputs store a blank
  `path`/`number` as `null` (sysmissing). The arg-value contract (sysmissing vs
  value; booleans strictly true/false) is documented in
  docs/cmdlet-data-formats.md "Editor metadata", and tri-state logic is deferred
  to a separate cmdlet family (docs/roadmap.md).

- **Fixed the projects-file path mismatch that made the online monitor show a
  false "project file changed" overlay everywhere except the Vite dev server.**
  Root cause: `config['db_file']` kept the raw CLI path (often relative) while
  `GET /qc/project` serves the resolved `db_file.resource_path`
  (`Path(...).resolve()`), so the header path and the API path never matched in
  the bundle. Fix is backend-only: `main_ui_program.py` stores the resolved
  path (`config['db_file'] = str(db_file.resource_path)`) and the home page
  header renders that same resolved `resource_path`, so header and API always
  serve the same string and the monitor's plain equality never false-positives.
  Path normalization happens once, at load time, inside the physical-file
  processors (`DBFileYaml`/`DBFileSqlite.__init__` — the only place that knows
  the resource is a file); `DBFile.__new__` was fixed to allocate the concrete
  processor via `object.__new__(DBFileCls)` so `__init__` (and hence path
  resolution) runs exactly once instead of twice. No JS path normalization: a
  resource path is an opaque string to the browser (could be a db id / network
  address), so the monitor compares exact backend strings. New rule
  `.clinerules/07-resource-paths.md`; tests in `tests/test_detect_type.py`
  (relative→resolved, single-init, `oledb://` not resolved) and the
  `background_onlineindicator` spec.

- **Simplified the project-settings modal heading.** Renamed the modal title
  "Project" → "Project settings" and shortened the subtitle to "Project name and
  description" (dropping the "shown in the page header" clause) in
  `src/frontend/app_js/src/app/project_settings/index.js`. No spec asserted on
  those strings, so no test change. Committed & pushed (`9af29f7`).

- **Standardized button hover animation to 500ms across the app.** Added
  `transition: 500ms all ease` to the remaining action-button base classes that
  had no transition (`.apqa-qcrules-page-button`, `.apqa-rule-form-button`,
  `.apqa-input-button`) and changed the two `600ms` buttons
  (`.mdm-git-ui-page-dismiss` and `.apqa-button-page-close`) to `500ms`. The
  modal `.apqa-button-close` was already 500ms, so all standard action buttons
  now animate uniformly. (Left the global-skin `.mdm-btn`/`.mdm-link-btn` link
  fade at 350ms — those are generic skin/link classes, not the app's action
  buttons.) 178 vitest tests pass. **Not committed yet — awaiting review.**

- **Unified modal footer buttons across all modals.** Took size/alignment from
  the project-settings footer (`min-width: 200px` + the shared
  `.apqa-modal-actions` responsive stack→row), the color scheme from the
  create-rule window (primary `#385` → hover `#1c6b3e`, staying green instead of
  reversing to white; secondary `#333` text / `#d0d0d0` border / hover `#999`),
  and a uniform `500ms all ease` animation. Switched the create-rule and
  delete-confirm modals onto the shared `.apqa-modal-actions` +
  `.apqa-button-close` classes (added `.apqa-button-danger` for the destructive
  confirm action, keeping its neutral→red hover), removed the now-unused
  delete-confirm button rules, and updated the delete-confirm spec selectors.
  178 vitest tests pass. **Not committed yet — awaiting review.**

- **Flattened modal footer button borders and reworked primary/secondary
  colors.** The footer buttons (`.apqa-button-close`) only set `border-color`,
  so the browser's default `outset` bevel rendered light left/top and dark
  right/bottom edges. Changed to `border: 1px solid #d0d0d0` with hover
  `border-color: #000` (secondary/cancel), and moved the primary style into
  `modals/styles.css` as `.apqa-button-close.apqa-button-primary`:
  `background: #385; border-color: #2c7d51; color: #fff`, reversing on hover to
  white background / `#385` border / `#217346` text with a faster `150ms all
  ease` transition (vs the secondary button's `600ms`). Removed the
  now-redundant project-settings-local `.apqa-button-primary` rules. 178 vitest
  tests pass.

- **Standardized modal footer actions: primary-left / cancel-right, responsive
  stack.** The shared `.apqa-modal-actions` footer (project settings, test page,
  iframe navbar modal) is now mobile-first: `display: flex; flex-direction:
  column; gap: 8px`, switching to a single `row` at `@container (min-width:
  420px)`; `.apqa-button-close` dropped its `margin: 14px auto 0 0` (now `0`).
  Made `.mdm-git-ui-modal-wrapper` a size container (`container-type:
  inline-size`) so the footer responds to the modal's own width. Reordered the
  buttons so the primary action is first/left and cancel is right: project
  settings (Save→Cancel), rule form (Create rule→Cancel), delete confirm
  (Delete→Cancel, now `justify-content: flex-start`). Updated the
  `project_settings` and `rule_delete_confirm` specs that assumed Cancel was the
  first button. 178 vitest tests pass.

- **Removed the extra vertical spacing above modal headings and under their
  description line.** Modal windows (project settings, test page, …) render
  their `h2` title through the global skin, which gives `h2` vertical padding —
  pushing the title 15px below the modal's own padding and adding a gap before
  the description. Centralized `.apqa-modal-form h2 { margin: 0; padding: 0 }`
  in `common_components/modals/styles.css`, and added a shared
  `.apqa-modal-form-subtitle { margin: 0; padding: 0 }` class for the first `p`
  below a modal heading (instead of blanket-overriding all `p`s). Applied
  `apqa-modal-form-subtitle` to the description paragraphs in
  `project_settings/index.js` and `testpage/index.js` (alongside their existing
  per-component typography classes), and removed the now-redundant
  `margin: 0` / `margin: 4px 0 0` from the per-component title/subtitle styles.
  178 vitest tests pass.

- **Aligned hardcoded component border-radius values with the new 7px button
  convention.** Replaced `border-radius: 4px` → `7px` across the QC-rule list
  buttons/inputs and entry boxes, rule form, project-settings input, records
  filter, and the shared input components (`input_cmdlet`, `input_comparison_op`,
  `input_gallery`, `input_multipunch`, `input_search_select`, `input_regex_text`,
  `input_qcrule_tags`, `pages`), plus the legacy pagination `6px` in
  `filter_records_form` → `7px`. Left intentionally round/special elements
  unchanged (badges/tags/pills/switches, dashed group boxes at 6px, 3px
  menu-option highlights, tabbed/rollable containers, modals/popups/panels).
  Components keep literal `7px` (not the `--mdm-border-radius` var) to stay
  self-contained/liftable. 178 vitest tests pass.

- **Added a reusable `mdm-link-btn` class to `common.css`** — a link styled as a
  bordered inline button (plain 1px `currentColor` border, transparent
  background, uniform padding, no underline/glow/outline, pointer cursor) that
  fades (350 ms ease) to `--mdm-color-primary` on hover/focus/active. Applied it
  to the `background_onlineindicator` "reload the page" link (replacing the old
  `apqa-online-monitor-reload` class and its styling) and overrode its
  hover/focus/active color to black in the component's `styles.css`. Updated
  `index.spec.js` to expect the new class and logged the change in
  `common.css.changelog.md`. Also increased `--mdm-border-radius` globally from
  4px to 7px and made `mdm-link-btn` use it (so the reload link now uses the
  standard button border radius).

- **Changed the default dev port from `5180` to `5280`** (a global find-and-replace
  across the tracked source/docs/tests): `src/webserver_config.py` `DEFAULT_PORT`,
  `dev_backend.py` `DEFAULT_PORT` + the `--config-webserver-port 5280` pin,
  `src/main_ui_program.py` dev notes, `src/frontend/app_js/vite.config.js` (all
  proxy targets), `docs/*`, `.clinerules/*`, and the two port-literal tests.
  Deliberately **not** changed: the vendored `remixicon.svg` (its `5180` is SVG
  glyph path data, not a port) and the `src/webserver_engine/webserve` submodule's
  `find_free_port(start=5180)` default (separate repo, and apqa always passes
  `start=` explicitly, so that default is unused by apqa). No submodule pointer
  moved.

- **`dev_backend.py` color-codes success/failure output; the webserver's fixed-port
  pre-check no longer false-fails on `TIME_WAIT`.**
  `dev_backend.py` now prints its human-readable outcome lines in green (success)
  / red (failure), emitted only when stdout is an interactive terminal and
  `NO_COLOR` is unset (VT enabled on Windows 10+): `start`/`restart`/`health`/
  `status` color by outcome, `stop` colors the "stopped…" lines green, and
  `logs`'s "no log file" is red. `src/webserver_config.py` `_port_is_free` now
  sets `SO_REUSEADDR` on POSIX (the real `HTTPServer` already sets
  `allow_reuse_address`), fixing the intermittent `dev_backend.py restart`
  "port already in use" failure from the roadmap. Updated the roadmap item
  (done), `docs/maintenance-log.md`, the `backend` skill, and added color tests.


- **Added a `/health` liveness endpoint + a full-screen "backend offline / project changed" overlay.**
  New `src/frontend/endpoints_health.py` (`handle_health`: `GET`/`HEAD` → 200,
  else 405) registered as `'/health'` in `src/endpoints.py`; the webserver engine
  already suppresses the body for `HEAD`, so one renderer serves both. Project
  identity is **not** a second endpoint — it reuses `GET /qc/project`'s existing
  `path` field (no top-level namespace pollution). Frontend: new
  `src/frontend/app_js/src/app/background_onlineindicator/` component (mounted in
  `app.js`) polls `HEAD /health` (offline → grey full-screen panel, mirroring
  gitgui's `background_onlineindicator` look) and `GET /qc/project` (path differs
  from the load-time path → red panel + reload link). The load-time path is read
  from `.apqaui-html-page-project-path` (server-rendered in the bundle), falling
  back to the first `/qc/project` response in the Vite dev server. `/health`
  added to the Vite proxy. Tests `tests/test_endpoints_health.py` +
  `background_onlineindicator/index.spec.js`. Validated: 866 Python tests + 178
  vitest tests pass, `build.sh` OK, and the live Vite page shows/hides the
  overlay when the backend is stopped/started.

- **Renamed the dev-backend runtime files to `.dev_backend.{pid,log}` and added
  `docs/cheatsheet.md` (follow-up to "dev: add backend control tooling…").**
  `dev_backend.py`'s pid/log constants, the `.gitignore` entries, the `backend`
  skill, and `docs/development.md` / `docs/maintenance-log.md` now reference
  `.dev_backend.pid` / `.dev_backend.log`. `docs/cheatsheet.md` is a new
  quick-reference for build / run / dev-backend / dev-test / frontend commands.


- **Removed the dead `vue` importmap from `src/frontend/app_js/index.html`.**
  `index.html` is Vite's entry point only — the backend-served app never loads
  it (it serves its own HTML via `make_html.py`), and in Vite dev mode `vue`
  resolves from `node_modules` via the `vite.config.js` alias. So the importmap
  in `index.html` was never used and was removed. The backend keeps its own,
  still-needed importmap in `endpoints_html_paths.py` (injected into the served
  HTML) that resolves the bundle's external `import ... from 'vue'` to
  `/assets/vendorlibs/vue.js` — that one stays. Updated `docs/development.md`
  (Dual run mode) to document this split.

- **Added `--config-webserver-port` (fixed / auto-increment / default 5280).**
  New `src/webserver_config.py` (`parse_webserver_port` + `select_webserver_port`)
  drives the port for the new `--config-webserver-port` flag on
  `src/main_ui_program.py`: `<port>` fails if occupied, `<port>+` auto-increments
  by one, and the default auto-increments from 5280 (the old `find_free_port`
  behavior). `dev_backend.py` now pins the port via `--config-webserver-port 5280`
  so the backend never drifts off Vite's hard-coded `localhost:5280` proxy target.
  The Vite note is recorded in code comments + `--help`. Tests
  `tests/test_webserver_config.py`; docs `docs/development.md` (Ports) +
  `docs/maintenance-log.md`. Validated: full Python suite 435 passed / 3 skipped
  (8 new port tests), `build.sh` OK, and both the bundle and the launcher reject
  an occupied fixed port and an invalid value with readable errors (exit 1).

- **Added cross-platform dev backend tooling + a `--browser` launch flag.**
  New `dev_backend.py` at the repo root is the single control point for the dev
  backend on `localhost:5280` (`status`/`start`/`stop`/`restart`/`health`/`logs`,
  stdlib-only, identical on Windows/macOS/Linux): it pins the port, starts
  headlessly, records the spawned PID in a gitignored `.apqa-dev-backend.pid`,
  and health-checks `http://localhost:5280/`. `src/main_ui_program.py` gained a
  `--browser` flag with `launch-system-default-browser` (default), `no-op`
  (skip the browser), and `pywebview` (declared but raises `NotImplementedError`);
  the decision lives in a new testable `src/browser_launcher.py`. A Cline skill
  (`.clinerules/skills/backend/`) plus a rule (`.clinerules/30-dev-backend-tooling.md`)
  point the agent at `dev_backend.py` and forbid `lsof`/`kill`/`sudo`. New tests
  `tests/test_browser_launcher.py` + `tests/test_dev_backend.py`. Docs:
  `docs/development.md` (Ports + dev backend tooling) and `docs/maintenance-log.md`.
  Validated: full Python suite 427 passed / 3 skipped (17 new tests), `build.sh`
  OK, and both the bundle and the launcher fail early on `--browser pywebview`.

- **Project name/path/description now live in the page header (roadmap item).**
  The header (`.apqaui-html-page-header`) gained a left brand column with the
  "apqaui app" wordmark (`#dfdfdf`) and, directly under it with no vertical
  gaps, three `#666` lines: database file path, project name, project
  description. All four rows share one size (14px) and weight (500), and are
  styled as plain text — no text-shadow/box-shadow/glow, transparency, underline
  or outline (explicit `text-shadow:none`, `opacity:1`, etc. on the brand
  rows). A gear icon (`ri-settings-3-line`) sits in the right column below
  the nav links and opens a new `project_settings` modal (name + description +
  Save), stored via `PUT /qc/project`. The page title is now
  `QC rules for <project name>` (fallback `QC rules`). Two rendering paths keep
  dev and bundle consistent: the backend server-renders the values in
  `endpoints_html_paths.py`, and a tiny `ProjectHeaderPopulator` (mounted in
  `app.js`) re-applies `GET /qc/project` client-side so the static Vite
  `index.html` header also fills in; the modal updates header + title in place
  (no full reload). `GET /qc/project` now also returns the `path` (from
  `db_file.resource_path`). New files under
  `src/frontend/app_js/src/app/project_settings/` (`index.js`, `styles.css`,
  `project_header.js`, `populator.js`, `index.spec.js`). Validated: backend
  837 passed, frontend 174 passed; full `build.sh` OK (bundle + `app.js` contain
  the new modal/populator). Note: the `<h1>` ("Manage QC rule list") was left
  unchanged — heading wording is the separate roadmap item #27.

- **Added project-level metadata to the rules database file (roadmap item).**
  The DB file now carries a single **project record** — `name`, `comment`, and
  an extensible `meta` bag — alongside `rules` and `groups`, in **both**
  supported formats. New `src/db_processors/project_base.py` defines the
  `Project` dataclass (`from_dict`/`to_dict`/`update`, all fields default
  empty). YAML stores it as the top-level `project:` mapping (absent in old
  files → defaults to an empty `Project`); SQLite stores it as a one-row
  `project` table (`id=1`, `name`/`comment` text, `meta` JSON), created and
  seeded in `_ensure_schema`/`_init_storage`. The base `DBFile` contract gained
  `get_project()`/`update_project()` plus a `.project` accessor. Exposed via a
  new `GET`/`PUT /qc/project` endpoint (`src/frontend/endpoints_project.py`,
  registered under `^/qc/project(?=$|/)`). Tests in
  `tests/test_db_processors_project.py` + `tests/test_endpoints_project.py`.
  Full suite: 408 passed / 3 skipped.

- **Removed the 2px vertical gap in the expanded rule head (verified, not
  blind).** `.apqa-qcrules-list-item-head` had `gap: 2px`, which the compact
  header (`.apqa-rule-compact-description`) does not — its unfinished note is
  forced onto its own line via `flex-basis: 100%` and sits flush under the name.
  Measured in the live page: expanded `name→note` gap was 2px while compact was
  0px; after removing the gap both are 0px, so the first line below the title no
  longer jumps down when a rule is expanded.


- **Aligned the expanded rule view's padding with the compact view (no jump on
  expand).** The full/expanded rule card (`.apqa-qcrules-list-item`, `rule.js`)
  was overriding the shared `.apqa-qcrules-entry` padding with `10px`, while the
  compact view used `6px 8px` — so toggling a rule expanded shifted the title,
  comment and definition right by 2px and down by 4px. `.apqa-qcrules-list-item`
  now uses `padding: 6px 8px`, so the bolded title and the comment line directly
  below it keep the same left indent as the collapsed state.


- **Added expand/collapse arrow icons to the rule name (roadmap item #8).** The
  compact/collapsed rule header (`rule_compact.js`, `.apqa-rule-compact-name`)
  now leads with a `ri-arrow-down-double-fill` (down-double) icon and the full/
  expanded header (`rule.js`, `.apqa-qcrules-list-item-name`) leads with a
  `ri-arrow-up-double-fill` (up-double) icon, so the click-to-toggle affordance
  on the rule title is visible instead of discoverable only by accident. Both
  `<i>` glyphs carry a shared `.apqa-rule-expand-icon` class (styles.css: grey
  `#999`, `font-weight: normal`, `font-size: 0.9em`, 6px right margin) and
  `aria-hidden="true"`, matching the folder `[+]/[-]` toggle in `rules_tree.js`.
  Uses the already-vendored Remix Icon font (linked in `app_js/index.html`). No
  state needed to be passed down: `RuleCompact` renders only when collapsed and
  `Rule` only when expanded. Added specs (`rule_compact.spec.js`,
  `rule_record.spec.js`). Validated: frontend Vitest 170 passed / 23 files (two
  new tests).


- **Added Remix Icon v4.9.0 as a vendored webfont asset** (mirrors the gitgui
  project). Downloaded `remixicon.css` + `.eot`/`.ttf`/`.woff`/`.woff2`/`.svg`
  plus `LICENSE.txt` and `README.md` into
  `src/frontend/assets_vendor_libs/fonts/remixicon/`; `build_templates.py`
  `build_vendorlibs` scans that folder exactly like the ibm-plex fonts and
  emits `_ASSETS_VENDORLIBS_FONTS_REMIXICON`.
  `src/frontend/endpoints_assets_delivery_path.py` serves it under
  `/assets/vendorlibs/fonts/remixicon/` (the CSS is linked in the HTML head via
  `make_default_assets_list` + `app_js/index.html`; the font files are loaded
  recursively from the CSS). Also extended `detect_content_type` to return
  proper font/SVG MIME types (`font/woff2`, `font/woff`, `font/ttf`,
  `font/otf`, `application/vnd.ms-fontobject`, `image/svg+xml`) — this also
  fixes the previously-`text/plain` content type for the ibm-plex fonts.
  License: Remix Icon License v1.0 (permissive; attribution optional).
   Gotcha: `build.sh` also has an explicit `cat ..._ASSETS_BUNDLED_PY.py >>
   src/frontend/GENERATED/ASSETS.py` list, so a new `_ASSETS_VENDORLIBS_FONTS_*`
   bundle must be appended there too — the first build after this change failed
   with `ImportError: cannot import name '_ASSETS_VENDORLIBS_FONTS_REMIXICON'`
   until the remixicon `cat` line was added to `build.sh`.



- **Fixed the `tagSuggestions` Vue render warning (roadmap item #11).**
  `QcRulesList` (`src/frontend/app_js/src/app/qcrules_list/index.js`) computed
  `tagSuggestions` and referenced it from the scoped-slot template
  (`:tag-suggestions="tagSuggestions"` on `rules-tree`) but never returned it
  from `setup()`, so Vue logged `Property "tagSuggestions" was accessed during
  render but is not defined on instance` whenever rules were rendered (the
  slot content is rendered inside `component-records-filter`, which is why the
  warning pointed at `ComponentRecordsFilter`). Added `tagSuggestions` to the
  returned object. Added `index.spec.js` — the first spec for the
  `QcRulesList` page component — which stubs `fetch` for `/qc/rules` +
  `/qc/groups` and asserts the distinct tags are passed to `RulesTree`; it
  fails (returns `[]`) without the fix and passes with it. Validated: frontend
  Vitest 168 passed / 23 files (one new test).

- **Reset the create-form technical id to auto-updating when cleared (roadmap
  item #9).** In `rule_form.js` `onIdInput`, emptying the id field (empty or
  whitespace-only) now sets `idTouched` back to `false` and immediately
  re-derives the id from the current display name via `makeUniqueSlug`,
  mirroring the existing `watch(name, …)` auto-fill. Previously a user who
  cleared the id stayed in manual mode and only got a re-derived id at submit
  time. Added a spec (`resumes auto-fill when the technical id is cleared`) and
  renamed the cleared-id test to `re-derives a deduplicated id when the id field
  is cleared`. Validated: frontend Vitest 167 passed / 22 files (one new test).

- **Implemented the field-access + shape-changing cmdlet set (roadmap item #10).**
  New middle processors: `select-field` (block → field value; array → flat list
  of that field per iteration, the JS `obj.field` / `items.map(x => x.field)`
  mental model), `select-item` (array element by zero-based `index`, negatives
  allowed), `select-range` (array sub-range `start` inclusive / `stop` exclusive,
  no step), `map` (ForEach-Object: `args.transform` is a cmdlet chain run per
  iteration with the iteration as its piped value), and `where` (filter:
  `args.predicate` is a cmdlet chain, an iteration is kept when its result is
  truthy via `bool()`). Registered in `src/cmdlets/__init__.py`; modules under
  `src/cmdlets/{select_field,select_item,select_range,map_,where}/`. Missing
  field / out-of-range / bad type all fail early with readable errors. `where`
  predicates stay limited to existing predicate/validation cmdlets until
  comparison-as-cmdlet lands (roadmap idea).

- **Added the `cmdlet-chain` arg type (a single cmdlet chain) and its editor.**
  `map`/`where` declare `transform`/`predicate` as type `cmdlet-chain` (distinct
  from the plural `cmdlet-chains` used by `and`/`or`/`bit-*` operands).
  `input_cmdlet` renders it as one `input_cmdlet_chain`; `input_cmdlet_chain`
  gained a `firstKinds` prop (default `['source']`) so callbacks pass
  `['processor','terminal']` (a callback's first cmdlet receives the iteration,
  so it must not be a source reader). Docs updated: `docs/cmdlet-data-formats.md`
  (naming + shape-changing sections, arg types, remaining-to-implement),
  `docs/development.md` (middle-processor list, `map`/`where` shapes, arg types);
  roadmap item #10 marked Done plus three new ideas (try-catch/error value,
  comparison-as-cmdlet, `select-item` by name). Naming note: `select-field` (and
  `map`/`where` vs `filter`/`foreach-object`) is provisional per the docs.
  Validated: backend `pytest tests/` 385 passed / 3 skipped (incl. new
  `tests/test_shape_cmdlets.py`, 34 tests); frontend Vitest 166 passed / 22 files
  (incl. new `cmdlet-chain`/`firstKinds` specs).

- **Adopted the `2x-` clinerules from `gitgui`.** Renamed
  `.clinerules/08-commit-messages.md` →
  `.clinerules/20-git-commit-messages-wording.md` and
  `.clinerules/11-submodules-commits.md` →
  `.clinerules/21-git-submodules-commits-order.md` (both content-updated to
  match gitgui's versions, which add an intro line/paragraph and a fuller
  title), and added `.clinerules/22-when-making-commits.md` and
  `.clinerules/29-github-issues.md` verbatim from gitgui. All four files are now
  byte-identical to `/Users/andrej/work/gitgui/.clinerules/`. Rules/docs only;
  no code change.

- **Documented the two ways to run the frontend (bundle vs Vite dev).** Added a
  "Dual run mode (npm dev vs bundle)" section to
  `.clinerules/02-frontend-build.md` and matching "Dual run mode (npm dev vs
  bundle)" + "Ports" subsections to `docs/development.md`, porting the principle
  from `gitgui` (its `.clinerules/02-frontend-build.md` and
  `docs/dev-docs.md`). Key points captured: the backend-served `py_js_bundler`
  bundle (`build.sh` → `src/frontend/GENERATED/app.js`, served at
  `/assets/app.js`) needs only Python; the Vite dev server (`npm install` +
  `npm run dev` in `src/frontend/app_js`) additionally needs Node and a running
  backend, and hard-codes `http://localhost:5280` in `vite.config.js`; every JS
  change must work under both modes. Also documented that the backend webserver
  accepts any HTTP method name while the npm/Vite dev server (Node `http` +
  `llhttp`) rejects non-standard method names with `400 Bad Request` — not a
  blocker for the bundle (no Node), but it can complicate development/tests.
  Docs/rules only; no code change.

- **Fixed broken `npm run dev` in `src/frontend/app_js`.** `node_modules/.bin/*`
  had been populated with *regular file copies* of each package's bin script
  instead of the symlinks npm creates (`-rwxr-xr-x` instead of
  `lrwxr-xr-x`). A copied `.bin/vite` resolves its relative
  `import('../dist/node/cli.js')` against `node_modules/dist/` (missing) rather
  than `node_modules/vite/dist/`, so `npm run dev` died with
  `ERR_MODULE_NOT_FOUND ... node_modules/dist/node/cli.js`. Reinstalled with
  `npm ci` in `src/frontend/app_js`, which recreated the symlinks
  (`.bin/vite -> ../vite/bin/vite.js` etc.); `npm run dev` now boots Vite
  v8.2.1 on `http://localhost:5173/`. This also fixes the previously-noted
  broken `node_modules/.bin/vitest` shim (now a symlink, so `npm run test:unit`
  should work directly again). **Gotcha:** if this repo's `node_modules` is ever
  restored from an archive/zip/checkpoint that dereferences symlinks, the bin
  shims break again — rerun `npm ci` (or re-`npm install`) in
  `src/frontend/app_js` to regenerate them.

- **Restricted the `input_gallery` textarea to vertical-only resize.** Added a
  `resize: vertical` rule for `.apqa-input-gallery textarea` in
  `input_gallery/styles.css`, so the test-page textarea can still be dragged
  taller/shorter from the bottom but its width stays fixed. Pure CSS; no
  template or spec change.

- **Clarified `docs/cmdlet-data-formats.md` around "Missing & duplicate names".**
  The title was ambiguous — "names" could be read as cmdlet names (there is a
  separate "Cmdlet naming" section) when the section actually specifies how
  source readers name **rows/columns** (fields/records) when reading tabular
  input (e.g. Excel) that may lack or repeat names. Retitled it to
  "Row & column names (missing or duplicate)", added a lead-in tying it to
  source readers, and updated the cross-reference in "Worked example: an Excel
  workbook". Also added a short "How to read this document" section after "Goal"
  splitting the doc into two groups — data formats (what cmdlets operate
  on/return) vs cmdlet behaviour (what individual cmdlets and the editor do) —
  so the two kinds of sections are explicit. Docs only; no code change (the
  section is a spec ahead of the current `get-content-excel` implementation,
  which only deduplicates headers and does no row naming yet).

- **Ported the regex-capable text input from gitgui and made it the default text
  filter in `RecordsFilter`.** New reusable component
  `common_components/input_regex_text` (registered in `app.js` as
  `component-input-regextext`): a normal text box with a `.*` toggle at the right
  inside the box, regex mode **off by default**. It emits `{ text, regex }` via
  `v-model` (also `input`/`change`/`focus`/`blur`), forwards `placeholder`/`name`
  to the inner input, and fully owns its look (`.apqa-input-regex-text*` classes)
  so it works standalone too. `RecordsFilter` now renders it for all text (and
  unspecified-type) columns instead of the plain `<input>`; `matchers.js`
  `matchText` and `summarizeFilters` understand the `{ text, regex }` value
  (regex → `new RegExp(text)`; invalid regex matches nothing; summary shows
  `/text/` when regex is on). Scoped the records-filter input CSS to
  `:not(.apqa-input-regex-text-input)` so it no longer overrides the component's
  own styling, and dropped the now-unused `.apqa-records-filter-field-input`
  class. New specs: `input_regex_text/index.spec.js` (5), plus regex cases in
  `records_filter/matchers.spec.js` and `records_filter/index.spec.js`.
  Validated: full JS suite 163 passed / 22 files, and `vite build` 96 modules.

- **Added `transform-text-regex`; settled the text-transform family prefix as `transform-`.**
  New processor cmdlet at `src/cmdlets/transform_text_regex/` registered as
  `transform-text-regex`: takes a text value and returns text, replacing every match of
  `args['pattern']` (a regex) with `args['replacement']` via Python's `re.sub`
  (so backreferences like `\1` work). Optional `case_insensitive` (bool) and
  `count` (number, default `0` = replace all). Mirrors the `matches`/`length`
  string helpers: raises `TypeError` on non-text (incl. `sysmissing`) and fails
  early on a missing `pattern`/`replacement`. Registered in
  `src/cmdlets/__init__.py`, tested in `tests/test_standard_cmdlets.py` (11 new
  tests), documented in `docs/cmdlet-data-formats.md` under "String helpers".
  Also renamed `format-strip-html` → `transform-strip-html` (module
  `src/cmdlets/format_strip_html/` → `transform_strip_html/`), settling the
  text-transform family prefix as `transform-`.
  Validated: full `tests/` suite 350 passed / 3 skipped.

- **Made modal content scroll uniformly (whole content, no sticky header).**
  The modal shell (`common_components/modals`) previously pinned the wrapper
  full-height and clipped the inner, so scrollability was bolted on per component
  and was inconsistent: the iframe navbar modals and the test page scrolled, but
  the create-QC-rule form did not (its `flex:0 1 auto; overflow:visible` chain
  plus a `min-height:auto` form child blocked the scrollbar). The shell now owns
  it: the wrapper is shrink-to-content and capped at `calc(100vh - 48px)`, and
  `.mdm-git-ui-modal-inner` is the single `overflow-y: auto` region, so every
  content modal scrolls its whole content when it does not fit (no sticky header).
  Removed the per-component `:has(...)` shrink/scroll hacks from `rule_form.css`
  and `testpage/styles.css`; kept one `:has(.apqa-ajax-pageview-form)` override so
  the iframe navbar modal stays full-height (iframes need a definite height to
  scroll internally). Validated: `vite build` 94 modules, 151 JS tests pass, the
  self-written `py_js_bundler` still bundles `app.js` (contains `overflow-y:auto`
  + `max-height:calc(100vh - 48px)`), and a real-browser harness confirmed the
  rule form scrolls end-to-end with the actions reachable, the iframe modal stays
  full-height, and the delete confirm stays a centered small box.

- **Added a "Test page" navbar link that opens a reusable form-control gallery
  modal.** New reusable `form_field` component
  (`common_components/form_field`: label above/beside the control + optional
  help/required marker, no forced widths) and an `input_gallery` catalog
  (`common_components/input_gallery`) that shows every native input type
  (text/number/date/time/file/color/range, selects, checkboxes, radios, toggle,
  buttons) plus the existing reusable inputs (`input_numeric_range`,
  `input_datetime_range`, `input_search_select`, `input_multipunch`). New
  `app/testpage` modal host opens the gallery directly (not via iframe): the
  header nav gains `<li navigation-role="testpage">…` with
  `data-open-vue-modal="testpage"`, and `manipulate_links.js` gained a small
  `VUE_MODALS` registry + handler that calls `createModal(TestPageModal)` for such
  links. `endpoints_html_paths.py` + dev `index.html` updated. Validated: 151 JS
  tests pass (2 new spec files), `vite build` 94 modules, and the self-written
  `py_js_bundler` still bundles `app.js` (contains the gallery + modal + handler).

- **Taught pinliner to emit an executable-bundle entry point; standardized
  entry-point imports to a two-branch `__package__` split.** pinliner now accepts
  `--main <module> --main-attr <attr>` and appends an `if __name__ == '__main__'`
  block that imports the module and calls its attribute, so the bundle runs
  `src.launcher.main()` without `build.sh` hand-patching `launcher.main()`.
  `build.sh` passes `--main src.launcher --main-attr main` and only appends the
  app-specific pytest entry point from `src_dev_build/bundle_pytest_postfix.py`.
  The entry-point modules (`src/launcher.py`, `src/main_ui_program.py`,
  `src/main_init_program.py`, `src/main_print_help.py`) select imports on
  `__package__`: relative inside `src`, flat with no parent package. Plain-script
  invocation (`python src/X.py`, without `-m`) is dropped (no `sys.path` bootstrap,
  no `src.*` absolute imports). pinliner README + `tests/test_inliner.py` updated.
  pinliner changes committed + pushed (`3c0ba17`, `7152465`); the
  `src_dev_build/lib/pinliner` gitlink is bumped to `7152465`.

- **Added `docs/maintenance-log.md`.** A cross-project log for structural changes
  shared by every repo of the same shape (launcher `--program` router + pinliner
  one-file bundle). First entry records the entry-point import/bundling/call
  convention; a second entry records the log's own creation. Repo-specific
  changes stay out of it (they live here and in the commit history).


- **Committed the `py_js_bundler` submodule bump and a new rule.** The
  `src/frontend/bundler_engine/lib/py_js_bundler` gitlink moved `a19bb77` →
  `09e4094` ("Support full ES6+ import/export syntax in bundler"); the target
  commit is on that submodule's `origin/main`, so it satisfies the new
  `.clinerules/11-submodules-commits.md` rule (a submodule pointer's target
  commit must exist on the submodule's own remote). Both were committed in
  `01388dd` on `main` (the two changes ended up in one commit after a parallel
  git-index race; the commit is fine and the working tree is clean).


- **Reworked `get-content-excel` to return a block of sheets (roadmap item).**
  Removed the unstable `sheet` arg; the cmdlet now reads the whole workbook and
  returns a block keyed by sheet name, each value an array of row blocks (header
  row = column names), closing the workbook in a `finally`. Sheet order is
  preserved (dict insertion order). This forces a QC rule to address a sheet by
  its stable name instead of relying on whatever sheet Excel saved as active.
  Tests in `tests/test_get_content_excel.py` (built with openpyxl, skipped via
  `pytest.importorskip` when absent); docs updated in
  `docs/cmdlet-data-formats.md` and `docs/roadmap.md` (marked done).

- **Added `get-content-text` source reader and a `get-content` proxy.** New
  `src/cmdlets/get_content_text/` (registered as `get-content-text`, a *source*)
  reads a text file into a single text value via the stdlib
  `pathlib.Path.read_text`; args `path` (required) and `encoding` (default
  `utf-8`). New `src/cmdlets/get_content/` registers `get-content` as a thin
  proxy that delegates to `get-content-text` and shares its arg schema (`ARGS`).
  Both use only the stdlib, carry comment-only `requirements.txt` files for
  build.sh discovery, and are covered by `tests/test_get_content_text.py` plus
  metadata/discoverability assertions in `tests/test_cmdlet_metadata.py` and
  `tests/test_optional_dependencies.py`.

- **Added two network cmdlets for verifying CDN/image availability.** New
  `src/cmdlets/get_content_network_fetch/` (registered as
  `get-content-network-fetch`, a *processor*) takes a URL from the **piped value**
  and returns a block `{status, body, headers}`; `urllib.request` is stdlib and the
  import is unguarded (no optional pip dep), with a comment-only `requirements.txt`
  for build.sh discovery. Args: `method` (default `GET`), `read_only` (bool, default
  `true` — non-`GET`/`HEAD` raises), and `timeout` (number, default `30`; added
  proactively so a dead CDN can't hang the whole QC run). Non-2xx responses are
  returned as a block (caught `urllib.error.HTTPError`) rather than raising.
  Only `http`/`https` schemes are accepted as a minimal safety guard. New
  `src/cmdlets/validate_network_request_result/` (registered as
  `validate-network-request-result`, a *terminal*) returns `True` iff the block's
  `status` is 2xx, and raises `TypeError`/`ValueError` when the input is not the
  fetch block's shape (dict with `status`/`body`/`headers`, `status` an int).
  Both registered in `src/cmdlets/__init__.py`. Tests in
  `tests/test_network_cmdlets.py` (mocked `urlopen`), plus metadata/kind and
  optional-deps-discoverability assertions. Security permission model recorded in
  `docs/roadmap.md` (future work, not implemented).

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
  no myers-diff.
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


- Added a `transform-strip-html` terminal cmdlet (`src/cmdlets/transform_strip_html/__init__.py`,
  registered in `src/cmdlets/__init__.py`) that removes HTML markup and leaves
  plain text (`how <i>would</i> you rate...` → `how would you rate...`). It uses
  `BeautifulSoup(..., "html.parser")`, so misformatted/unbalanced markup is parsed
  best-effort instead of rejected. `sysmissing` → `""`; blocks/arrays recurse and
  keep their shape; other scalars delegate to the existing `as-text`.
  `beautifulsoup4` is an **optional dependency** — a per-cmdlet `requirements.txt`
  (`beautifulsoup4>=4`) plus the guarded-import pattern (the cmdlet is always
  registered and only raises a readable `ImportError` when run without the dep).
  The family prefix was settled as `transform-` (renamed from `format-`); see `docs/roadmap.md`. Tests in
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

- Entry-point modules (`src/launcher.py` + the starter scripts it dispatches to)
  select imports on `__package__` — relative inside `src`, flat otherwise. Run
  them via the bundle or `python -m src.X`; plain `python src/X.py` (without
  `-m`) is not supported.
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


# TODOs

This sections is to capture everything that comes to mind that should ideally be updated. Tasks listed here are not necessarily the highest priority.

- Library of typical patterns - already predefined chain of cmdlets, where the user must only add missing defs, like path to input file

- Finally, develop the pattern for "aliases"

- Buttons to add a new rule within folder, duplicate a rule...

- (open question) User settings storage/scope: `src/user_settings.py` `UserSettings` is currently an in-memory placeholder held on the session `config` (`config['user_settings']`) — nothing is persisted yet. Undecided whether it belongs to the user globally, to the project, or to a user x project combination, and where it lives (database, local file, json). Until decided, it only carries the permission-group allow-list gating cmdlet execution.

- (done — see `docs/qc-results-reporting.md`) Error visibility: a failing cmdlet now raises a `ChainError` naming the chain step (original exception chained as `__cause__`), and a *false* rule result now carries **diagnostic notes** with a data path (which field, which iteration) via `src/cmdlets/diagnostic.py` and `run_rule_with_report`; `validate-xml-compatible` records per-leaf notes.

- (idea, not final) Rule-editor ergonomics for entering chains of `select-field`: autofocus the `field` input when `select-field` is chosen and let Enter append the next `select-field` (focusing its input), so a nested path (`Fields -> SnifferData -> Fields -> Cluster -> …`) is typed as one keyboard flow instead of re-picking `select-field` from the drop-down each step.

- (idea, unclear) Auto-suggestion machinery for the cmdlet chain editor: at the root prefer `get-content-*` source readers (more common) over the equally-valid but rarer `logical-*`; let each cmdlet declare its most expected successor (object-returning cmdlets most often lead to `select-field`); pin `select-field` first in the processor drop-down. No clear answer yet — record only, implement nothing.

- (idea, rejected for now) Pre-fill `select-field`'s `field` value with the actual field names of the piped object. Rejected because it would require a pre-flight run of the upstream cmdlets (filesystem read on `.mdd`/`.xlsx`, network request, …) — blocking side effects the editor must not trigger.


- edit cmdlet ui / literal: when "unset" is clicked, the input box should turn grey, like readonly/disabled and not clickable, until "unset" is unchecked.

- Not sure how to indicate in in design in `src/cmdlets`, but not show a placeholder for follow up cmdlet from a "literal value" cmdlet - it does not make sense. After the transformation of literal value, we can only get literal value, static - then, why not just enter that final value directly? We probably don't need a suggestion for next cmdlet in a chain.

- (remote db) Credentials for a remote SQL database are passed in ``--db-file`` as part of the SQLAlchemy URL (``postgresql://user:pass@host:port/db``). They are masked (password hidden) in everything the app stores/serves, but they still appear in the process command line / shell history. Consider a safer mechanism (an env var, a token file, or an interactive prompt) for future use.

- (qcrules_list UI) Nested cmdlet args: some `args` values are whole cmdlets or whole chains (e.g. the logical `logical-and`/`logical-or`/`bitwise-*` `operands`, `map`'s `transform`, `where`'s `predicate`). They currently render as a single `JSON.stringify`d blob and are styled as one non-breakable `.apqa-cmdlet-part` (`white-space: nowrap`), so a long nested chain does not wrap and overflows/overlaps. Needs a proper approach — e.g. render `cmdlet-chain`/`cmdlet-chains`-typed args with the real `CmdletChain` component (or a compact variant) instead of a JSON blob, and/or relax the no-wrap rule for those arg types so they can wrap between tokens.

- (fully resolved) red errors in run_ui.bat, can't find requirements.txt files with optional dependencies; also, redo the pattern to avoid making an "optional dependencies" directory within dist, can we simplify and embed all dependencies within the .sh and .bat scripts during the build stage? (Done: `build.sh` no longer copies a `dist/optional_dependencies/` folder; `build_templates.py --program transform-run-script` inlines each cmdlet's installable requirements as `pip install` statements into `dist/run_init.sh`/`dist/run_init.bat`, fixing the Windows `for /r` file-not-found errors.)
- (some updates are made but needs to be verified) (super important, not necessarily the first thing to focus on but one of the most important at the moment) cmdlet to get a property/field of an object - the most basic thing in this design - I was not able to find such. (Updates were made but were not verified: `select-field` reads one field from a block / a flat list from an array; `select-item` picks an array element by index; `select-range` takes a sub-range. Naming is still provisional — see docs/cmdlet-data-formats.md.)
- (in progress — declarative basics done, enforcement still future) Security: a permission/capability model for cmdlets that touch the outside world. Cmdlets now declare a `permissions` metadata list at registration — `filesystem` for the file readers (`get-content`, `get-content-text`, `get-content-excel`, `get-content-mdd`) and `network` for the network fetch (`get-content-network-fetch`); every other cmdlet is empty. It is served by `GET /cmdlets/metadata`. Still to do: a globally configured allow-list of granted permissions, and run-time enforcement so a cmdlet whose required permission is not granted fails with a readable error. Until then `get-content-network-fetch` only enforces the minimal `http`/`https` scheme guard plus the `read_only` method restriction (default `GET`/`HEAD`).
- (idea) try-catch / error value: a cmdlet exception currently aborts the whole rule at the failing step — there is no way to catch a failure and continue. Consider adding an **error value type** alongside `sysmissing` that carries failure info (message, source cmdlet, …) and a `try-catch` (or `attempt`/`recover`) cmdlet, so a failed step (e.g. a missing column) can be handled as a value instead of aborting. This is the future escape hatch for the "missing field raises" behaviour of `select-field`.
- (idea) tri-state logic cmdlets: booleans are kept strictly two-valued (`true`/`false`) because a three-valued boolean (true/false/unknown) is harder to reason about, while `sysmissing` still lets data be absent. If three-valued logic is needed, add a *separate* cmdlet family (three-valued `and`/`or`/`not`, comparisons, …) with its own naming prefix so it never collides with the two-valued `logical-*` booleans. See docs/cmdlet-data-formats.md "Editor metadata" → "Arg values: `sysmissing` vs value".
- (fully resolved) highlight unrecognized cmdlets differently: a rule whose chain references a cmdlet/op name not registered in the current environment is deliberately *not* marked "unfinished" (the name is a value, not `sysmissing`), so it fails at run time instead. (Done: added a derived `invalid` mark — `qcrules_list/grouping.js` `isInvalid`/`ruleInvalidProblems` flags unknown cmdlet names (recursively into nested chains, plus non-`{cmdlet,args}` steps) and unknown comparison-op names; it renders as a badge with a `title` tooltip, a grey helper note under the rule's name, and a pale-pink entry highlight distinct from `unfinished`.)
- Review list of "source reader" type cmdlets. First I was surprised "logical-and" and "logical-or" are listed as available, then I realized it really makes sense. But need a solid decision if "logical-and", "logical-or" and similar can be first in a chain.
- (fully resolved) Review possible ways to clean up "create new qc rule" dialog - too many fields, should be shown less by default, so that user is more focused. (Done: the create and edit QC rule forms now group their fields into three unlabeled sections — QC rule ID/name/comment, left/comparison/right, tags/markers — and the technical id ("QC rule ID") is shown collapsed as a one-line dark-grey value with a double-arrow toggle that expands into the editable/read-only input; it always sits above the name and auto-updates from the name on create.)
- `src/tstsuite.py` - review when aliases are run. When test are collectied? When module is loaded?
- QC rules - ensure alias can also be used instead of source read cmdlet, not just as a value for args.
- Decide the alias substitution - if we substitute every string with exact matches, or require special char, or make more structural syntax for this.
- We currently have the run-rule endpoint that receives a rule in json - review how would it work with aliases and what should we do to implement alias substitution.
- Continue implementation - edit qc rule, test run the qc rule, delete/rename/move rules, etc... (creating a rule via the modal form is now done; the rest of the CRUD UI — edit/run/delete/rename/move — is still pending)
- (some steps are taken, maybe can mark as resolved - please take a second look) Reconsider the name and common prefix for text-formatting (markup-to-text) cmdlets. (Done: the family prefix is now `transform-` — `format-strip-html` became `transform-strip-html`, and the new regex-replace cmdlet is `transform-text-regex`.)
- (partaially - started) Implement exact cmdlets and providers - that read Excel, CSV, SPSS, retrieve rows, object fields, etc...
- (getting really close to this, as of 10/24/2026) Go ahead and try on real project, and then update the list here with all key findings.
- (ideally, not first priority) Word-wrap in chain of cmdlets: fixed — each cmdlet name and argument now renders
  as its own no-wrap unit, the chain wraps between units (no more mid-word breaks),
  and an overlong part (e.g. a long `path=` param) is cut with an ellipsis on the
  right. Possible improvements left: (a) a dedicated "Windows Explorer"-style path
  truncation component that keeps the start and the trailing file name and collapses
  the middle, re-measuring on resize; (b) extract the `nowrap + ellipsis` style into
  a shared utility class once a second consumer appears.

- (done) Renamed the path-removal cmdlet: `filter` → `exclude-child` (shallow,
  direct children only) + `exclude-deep-node` (recursive), with a structured
  `rules` arg (`{name, type: eq|startswith|endswith|contains|regex, pattern,
  case_insensitive}`) and a new `path-rules` arg type/editor. Matching is now
  **relative** to the received value — the old full-path behaviour and the
  `navigation.py` path machinery were dropped as unnecessary.

- (done) Added the `include-*` pair (`include-child`, `include-deep-node`) as
  the keep-complement of `exclude-*`, reusing the same `path-rules` arg; both
  return `sysmissing` when nothing is kept.

## Random thougds and things to compare

- safe yaml

# TODOs

This sections is to capture everything that comes to mind that should ideally be updated. Tasks listed here are not necessarily the highest priority.

- (http db) Credentials for the remote HTTP database are passed in ``--db-file`` (``http://user:pass@host:port``). They are stripped from everything the app stores/serves, but they still appear in the process command line / shell history. Consider a safer mechanism (an env var, a token file, or an interactive prompt) for future use.

- (qcrules_list UI) Nested cmdlet args: some `args` values are whole cmdlets or whole chains (e.g. the logical `logical-and`/`logical-or`/`bitwise-*` `operands`, `map`'s `transform`, `where`'s `predicate`). They currently render as a single `JSON.stringify`d blob and are styled as one non-breakable `.apqa-cmdlet-part` (`white-space: nowrap`), so a long nested chain does not wrap and overflows/overlaps. Needs a proper approach — e.g. render `cmdlet-chain`/`cmdlet-chains`-typed args with the real `CmdletChain` component (or a compact variant) instead of a JSON blob, and/or relax the no-wrap rule for those arg types so they can wrap between tokens.

- (need to confirm the issue is still present) red errors in run_ui.bat, can't find requirements.txt files with optional dependencies; also, redo the pattern to avoid making an "optional dependencies" directory within dist, can we simplify and embed all dependencies within the .sh and .bat scripts during the build stage?
- (some updates are made but needs to be verified) (super important, not necessarily the first thing to focus on but one of the most important at the moment) cmdlet to get a property/field of an object - the most basic thing in this design - I was not able to find such. (Updates were made but were not verified: `select-field` reads one field from a block / a flat list from an array; `select-item` picks an array element by index; `select-range` takes a sub-range. Naming is still provisional — see docs/cmdlet-data-formats.md.)
- (lower priority, theoretical plans for future) Security: introduce a permission/capability model for cmdlets that touch the outside world. `get-content-network-fetch` (and any future network/IO cmdlet) should declare a required permission (e.g. `network`), the program should keep a globally configured allow-list of granted permissions, and a cmdlet whose permission is not granted must fail with a readable error at run time. For now the cmdlet only enforces a minimal `http`/`https` scheme guard plus the `read_only` method restriction (default `GET`/`HEAD`) — no permission groups yet.
- (idea) try-catch / error value: a cmdlet exception currently aborts the whole rule at the failing step — there is no way to catch a failure and continue. Consider adding an **error value type** alongside `sysmissing` that carries failure info (message, source cmdlet, …) and a `try-catch` (or `attempt`/`recover`) cmdlet, so a failed step (e.g. a missing column) can be handled as a value instead of aborting. This is the future escape hatch for the "missing field raises" behaviour of `select-field`.
- (idea) tri-state logic cmdlets: booleans are kept strictly two-valued (`true`/`false`) because a three-valued boolean (true/false/unknown) is harder to reason about, while `sysmissing` still lets data be absent. If three-valued logic is needed, add a *separate* cmdlet family (three-valued `and`/`or`/`not`, comparisons, …) with its own naming prefix so it never collides with the two-valued `logical-*` booleans. See docs/cmdlet-data-formats.md "Editor metadata" → "Arg values: `sysmissing` vs value".
- (idea) highlight unrecognized cmdlets differently: a rule whose chain references a cmdlet/op name not registered in the current environment is deliberately *not* marked "unfinished" (the name is a value, not `sysmissing`), so it fails at run time instead. Consider a separate visual technique (e.g. a distinct "unknown cmdlet" badge/color) to surface such rules without conflating them with the unfinished state.
- Review list of "source reader" type cmdlets. First I was surprised "logical-and" and "logical-or" are listed as available, then I realized it really makes sense. But need a solid decision if "logical-and", "logical-or" and similar can be first in a chain.
- Review possible ways to clean up "create new qc rule" dialog - too many fields, should be shown less by default, so that user is more focused. The qc rule name, shown in ui, is anyway necessary. The technical name can be hidden, but possible to unhide or show again with "v" and "^". The main with "Left side", "cmp op", and "Right side", should take the majority of screen. However, all other fields - comment, tags, labels, marks, etc - we should consider... Moving them somewhere out of focus area. Not sure where exactly. Like make it look like it's additional fields, not the key fields.
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

## Random thougds and things to compare

- safe yaml

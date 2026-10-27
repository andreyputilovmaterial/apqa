# TODOs

This sections is to capture everything that comes to mind that should ideally be updated. Tasks listed here are not necessarily the highest priority.

- get-content-excel cmdlet: remove the "sheet" arg, make it return deeper shape, so that it returns a collection of sheets. The author of new qc rule must specify the address explicitly, including sheet name - not imply program reads from last saved, that is not stable.
- Review list of "source reader" type cmdlets. First I was surprised "and" and "or" are listed as available, then I realized it really makes sense. But need a solid decision if "and", "or" and similar can be first in a chain.
- Review possible ways to clean up "create new qc rule" dialog - too many fields, should be shown less by default, so that user is more focused. The qc rule name, shown in ui, is anyway necessary. The technical name can be hidden, but possible to unhide or show again with "v" and "^". The main with "Left side", "cmp op", and "Right side", should take the majority of screen. However, all other fields - comment, tags, labels, marks, etc - we should consider... Moving them somewhere out of focus area. Not sure where exactly. Like make it look like it's additional fields, not the key fields.
- Id assinged to new qc rule is not verified to be unique. It should be updated both in ui, so that a generated slug has some addition to avoid repeating what already exists. And it must raise an error on backend side when we try to insert a rule with existing id.
- The heading and page title should be reviewed - I don't like the ording "Manage QC rules". The titles should only describe what is below, without any unnecessary suggestions for activities, like "manage". If the content below is a list of qc rules, the heading should just say it, list of qc rules. Or, better, without list: what you see below are qc rules, so heading should just say "qc rules". This both applies to headings on a page and overall page title. Then, after the update and simplification, two headings will be saying the same, will be effectively duplicates of each other - consider updated wording for each or remove/hide one of this.
- `src/tstsuite.py` - review when aliases are run. When test are collectied? When module is loaded?
- QC rules - ensure alias can also be used instead of source read cmdlet, not just as a value for args.
- Highlight the "unfinished" qc rules. Force them to have some "skip" mark. If some part or cmp op is missing, the rule can't be run - we must require the "skip" or some mark to mark it as unfinished. Rules that do not run or have special marks should be highlighted in color in qc rule list.
- Review the "the 4 `myers-diff` suites fail on a pre-existing module-resolution error, unrelated)" issue.
- Decide the alias substitution - if we substitute every string with exact matches, or require special char, or make more structural syntax for this.
- We currently have the run-rule endpoint that receives a rule in json - review how would it work with aliases and what should we do to implement alias substitution.
- Continue implementation - edit qc rule, test run the qc rule, delete/rename/move rules, etc... (creating a rule via the modal form is now done; the rest of the CRUD UI — edit/run/delete/rename/move — is still pending)
- Online status indicator
- Reconsider the name and common prefix for text-formatting (markup-to-text) cmdlets. `format-strip-html` was added as the first member, but `strip` alone is both too narrow (it names a single op) and too vague (it doesn't say the domain — stripping tags from text vs. stripping sensitive data from files), while `format` is only a placeholder for a "formatting update". Candidates: `text-…` or `format-…`. Decide the family name before adding more cmdlets of this kind.
- (partaially - started) Implement exact cmdlets and providers - that read Excel, CSV, SPSS, retrieve rows, object fields, etc...
- (getting really close to this, as of 10/24/2026) Go ahead and try on real project, and then update the list here with all key findings.
- (will check soon once implement other basic functions) Condensed form of records filtering component - review when pagination controls are visible, in condensed or expanded mode.
- (ideally, not first priority) Word-wrap in chain of cmdlets: fixed — each cmdlet name and argument now renders
  as its own no-wrap unit, the chain wraps between units (no more mid-word breaks),
  and an overlong part (e.g. a long `path=` param) is cut with an ellipsis on the
  right. Possible improvements left: (a) a dedicated "Windows Explorer"-style path
  truncation component that keeps the start and the trailing file name and collapses
  the middle, re-measuring on resize; (b) extract the `nowrap + ellipsis` style into
  a shared utility class once a second consumer appears.


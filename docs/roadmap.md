# TODOs

This sections is to capture everything that comes to mind that should ideally be updated. Tasks listed here are not necessarily the highest priority.

- Decide the alias substitution - if we substitute every string with exact matches, or require special char, or make more structural syntax for this.
- We currently have the run-rule endpoint that receives a rule in json - review how would it work with aliases and what should we do to implement alias substitution.
- (done) Make foldable groups for qc rules
- Continue implementation - edit qc rule, test run the qc rule, add or remove qc rules, etc...
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


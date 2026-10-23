# TODOs

This sections is to capture everything that comes to mind that should ideally be updated. Tasks listed here are not necessarily the highest priority.

- Make foldable groups for qc rules - otherwise it would be an enornous list
- Also make way more compact view of qc rule list - current view is way too spacious. Only 3 rules fit the screen by default, not suitable for maintaining big number of rules.
- Continue implementation - edit qc rule, test run the qc rule, add or remove qc rules, etc...
- Implement exact cmdlets and providers - that read Excel, CSV, SPSS, retrieve rows, object fields, etc...
- Go ahead and try on real project, and then update the list here with all key findings.
- Update list of qc rules (make it compact) and introduce global definitions/aliases. When I launch the ui, I see a list of qc rules, it's fine. I want to maintain a list of global (within project - stored in same database file or yaml as list of rules) "alias" definitions. For example, instead of passing path to `/project/p123/data/datafile.db`, I want to specify `/project/p123/data/datafile.db` as `PROCESSED_DATA`, and then pass `PROCESSED_DATA` as path param to cmdlets. So, I want the ui to be: first section lists those aliases. Similar list with filtering. Then below this actual qc rules should be listed. All should be somewhat compact, without much indents between section. Should look like just a raw list of definitions or rules. For rules, use the compact view. However, once clicked, it is revealved as full view. Click on header condenses the rule into compcat view again. I think there should be some wrapper component for "record", that renders both states, condensed or full, cinditionally, toggled with a click on header. As inner content of this record, I think another wrapper is needed, that implements "edit" button and shows actual qc rule component.
- Condensed form of records filtering component - review when pagination controls are visible, in condensed or expanded mode.
- Word-wrap in chain of cmdlets: fixed — each cmdlet name and argument now renders
  as its own no-wrap unit, the chain wraps between units (no more mid-word breaks),
  and an overlong part (e.g. a long `path=` param) is cut with an ellipsis on the
  right. Possible improvements left: (a) a dedicated "Windows Explorer"-style path
  truncation component that keeps the start and the trailing file name and collapses
  the middle, re-measuring on resize; (b) extract the `nowrap + ellipsis` style into
  a shared utility class once a second consumer appears.
- "Tags", in records filtering component - make it a multi-punch drop down. So that, on click, it expands similar to "not sorted" and "descending", but when expanded user can put ticks at necessary labels. CLick outside to close the drop down. That multi-punch drop down should be implemented as global component, not some special functionality of records filtering component. The records filtering component should only receive a short hint on expected data type within column - if it's just text, numeric field, date/time, or multi-punch with provided set of possible values.


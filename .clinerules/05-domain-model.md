# QC rule domain model

A QC rule has three essential parts: **left side**, **comparison op**, **right side**.

- Left and right sides are **chains of cmdlets** (PowerShell-like pipes), e.g.:
  `get-content Specs.xlsx | select-sheet "Title Details" | select-column "B" | count`
- Stored shape of a cmdlet: `{ cmdlet: <name>, args: { <param>: <value>, ... } }`. `args` is always a named mapping (flags like `-Recurse` become `{ recurse: true }`) and may be omitted when empty.
- Stored shape of a rule: `name` (unique identity), `meta` (extensible: `created_by`, `created_at`, `modified_at`, `comment`, `tags`, `markers`, …), `left` (list of cmdlets), `op` (string), `right` (list of cmdlets).
- `op` is a **registered comparison op name**, always scalar vs scalar (e.g. `eq`, `lt`, `gt`, `contains`).
- Three cmdlet types: (1) source readers, (2) middle processors (`select-column`, `map`, `count`, `to-string`, …), (3) terminal → scalar for comparison.
- Cmdlets are defined through a **global registry** (plugin-like) and are extensible — especially type-1 source readers.
- Prefer a **minimal but flexible** set of middle/terminal cmdlets; avoid source-specific cmdlets (no dedicated "read-excel-sheet"). One generic operation should work across Excel/SPSS/DB/etc.
- Scalar types a cmdlet can return: text, int, float, bool, date/time, single-punch categorical, multi-punch categorical. Compound types (object with named fields, collection of uniform objects, tuple) are still being finalized.
- **Every value may be `sysmissing`**, regardless of its type.
- In comparison, `sysmissing` is undefined/uncertain: it equals only another `sysmissing`. Comparing `sysmissing` to empty set/collection, zero, `false`, or empty string must return `false`.
- The same design principles apply to: the DB storage format, the UI, and what flows through the pipe.
- Rules may carry pytest modifiers in `meta.markers`: `skip` (do not run) and `xfail` (a failure is expected and treated as normal).

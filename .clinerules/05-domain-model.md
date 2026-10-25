# QC rule domain model

> The authoritative spec for value formats, comparison semantics, and cmdlet
> naming is `docs/cmdlet-data-formats.md`; this file is a condensed summary.

A QC rule has three essential parts: **left side**, **comparison op**, **right side**.

- Left and right sides are **chains of cmdlets** (PowerShell-like pipes), e.g.:
  `get-content Specs.xlsx | select-item "Title Details" | select-property "B" | count`
- Stored shape of a cmdlet: `{ cmdlet: <name>, args: { <param>: <value>, ... } }`. `args` is always a named mapping (flags like `-Recurse` become `{ recurse: true }`) and may be omitted when empty. `args` values are not restricted to strings — they may be numbers, booleans, lists, objects, or nested cmdlet chains.
- Stored shape of a rule: `name` (unique identity), `meta` (extensible: `created_by`, `created_at`, `modified_at`, `comment`, `tags`, `markers`, …), `left` (list of cmdlets), `op` (string), `op_args` (optional mapping), `right` (list of cmdlets).
- `op` is a **registered comparison op name** (e.g. `eq`, `ne`, `eq-unordered`, `lt`, `gt`, `contains`). `eq`/`ne` compare compound values deeply (blocks by name, order-insensitive; arrays in strict order); ordering ops (`lt`/`le`/`gt`/`ge`) are scalar-only. `op_args` (optional) passes op-specific options; `eq`/`ne` accept `op_args: { unordered_arrays: true }` for order-agnostic array comparison (`eq-unordered` is that flag hard-wired).
- Three cmdlet types: (1) source readers, (2) middle processors (`select-property`, `select-properties`, `select-item`, `where`, `map`, `sort`, `count`, `to-string`, …), (3) terminal → value for comparison.
- Cmdlets are defined through a **global registry** (plugin-like) and are extensible — especially type-1 source readers.
- Prefer a **minimal but flexible** set of middle/terminal cmdlets; avoid source-specific cmdlets (no dedicated "read-excel-sheet"). One generic operation should work across Excel/SPSS/DB/etc.
- Scalar types a cmdlet can return: text, int, float, bool, path, date/time, single-punch categorical, multi-punch categorical. Compound types: block (named fields), named collection (provisional), array (block repeated per iteration).
- **Every value may be `sysmissing`**, regardless of its type.
- In comparison, `sysmissing` is undefined/uncertain: it equals only another `sysmissing`. Comparing `sysmissing` to empty set/collection, zero, `false`, or empty string must return `false`.
- The same design principles apply to: the DB storage format, the UI, and what flows through the pipe.
- Rules may carry pytest modifiers in `meta.markers`: `skip` (do not run) and `xfail` (a failure is expected and treated as normal).
- Planned (not implemented): a **conditional marker** to skip a rule only on certain platforms/tools (e.g. Windows-only rules for `pywin32`), driven by an env var set by the outer `run_*.sh`/`.bat` script.

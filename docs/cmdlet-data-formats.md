# Cmdlet data formats

> Status: **draft specification — for review.** The runner (`src/rule_runner.py`),
> the cmdlet registry, and the comparison ops are already implemented. The typed
> value model below is **not yet implemented**: the runner and comparison ops
> currently work on plain Python values plus the `sysmissing` sentinel. This
> document is the proposal we need to align on before building the full cmdlet
> set on top of it.

## Goal

Cmdlets pass a single value down the pipe, and the comparison op consumes two of
those values. So that any cmdlet can follow any other — regardless of the source
data (Excel, CSV, SPSS, a database, …) — we need a **small, uniform, closed set
of value formats**. Once this set is final, a generic cmdlet such as "select a
field" can work identically on a sheet, a table, a query result, etc.

The same design applies to the DB storage format, the UI, and the values that
flow through the pipe.

## Scalar types

A cmdlet may produce/accept these scalar values:

| Type | Notes |
| --- | --- |
| text | |
| integer | |
| real / floating-point | |
| boolean | |
| date/time | |
| categorical (single-punch) | carries the set of available options |
| categorical (multi-punch) | carries the list of available punches |

Every scalar type may additionally be **`sysmissing`** — the value is allowed to
be "missing" for any type (like `NULL` in a database column), not only for
types that are conventionally nullable.

## `sysmissing`

- A single sentinel value, distinct from `None`, `0`, `False`, `""`, and the
  empty collection.
- In comparison it is undefined/uncertain:
  - `sysmissing == sysmissing` → `true`
  - `sysmissing` vs anything else (empty set, zero, `false`, empty string) → `false`
  - ordering (`<`, `<=`, `>`, `>=`) with `sysmissing` on either side → `false`
  - `contains` with `sysmissing` on either side → `false`

## Compound types

Three compound types, which may nest (a field may itself be scalar or compound):

1. **block** — a collection of named fields. Each field has a name and a value
   of any scalar or compound type. Fields are selected by name (like
   `record.field["state"]`).

2. **named collection** — the repeating pattern of Python's `namedtuple`: a
   fixed set of named fields, plus positional access. Cmdlets can select an
   element by index **and** by name.

3. **loop / grid / array** *(final name TBD)* — a **block** repeated for each
   iteration. Each iteration:
   - is always a block of fields (a loop of bare integers is **not** possible —
     to represent an array of ints you define a block with one integer column
     and a loop of such blocks);
   - can be accessed by index;
   - can also be accessed by name when every record has a unique key (the record
     name in the collection). Every database record is assumed to have such a key.

## Worked example: an Excel workbook

- The workbook is a **loop/grid/array of sheets**; each iteration (sheet) has
  both a name and an index.
- Each sheet is a **loop/grid/array of rows**; each iteration (row) has an index
  and a name (the name is read from an "index" column — assume it exists; what
  to do when it does not is still to be decided).
- Each row is a **block** whose fields are the sheet's columns. Assume column
  names are read from row 1 and are unique; resolving non-unique names is a
  later decision.
- `record.field["state"]` reads one field; there is no ambiguity from multiple
  "state" columns.

## Shape-changing operations (intent for future cmdlets)

On a loop/grid/array:

- **filter rows** → a loop/grid/array again, with the same field shape.
- **select one row** → a **block** (one field per column).
- **filter columns** → a loop/grid/array again, with a smaller field shape.
- **select one column** → the same as filtering columns down to that one column:
  a loop/grid/array whose block has a single field.

## Naming note (TBD)

The names `select-row` / `select-column` are provisional and probably wrong:
they describe the *shape* of the object, not its meaning. A workbook's
"iterations" are sheets, a sheet's "iterations" are rows. We need shape-agnostic
names (e.g. "select field by name / by index", "filter iterations", "select
iteration") — to be decided once the format above is confirmed.

## Open questions

- Final naming of the compound types (especially "loop" vs "grid" vs "array").
- Exact Python / JSON / DB / UI representation of each type (and of `sysmissing`).
- Whether comparison ops should be type-strict (e.g. `0 == false`?).
- How to read a row's name when the source has no "index" column.
- How to resolve non-unique column names.

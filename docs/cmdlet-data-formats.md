# Cmdlet data formats

> Status: **agreed specification.** The runner (`src/rule_runner.py`), the cmdlet
> registry, and the comparison ops are implemented and follow this spec. The typed
> *value objects* (categoricals, and the block / named collection / array
> wrappers) are **not yet implemented** — until they are, the same rules are
> expressed with plain Python values (`None` for `sysmissing`, `dict` for a block,
> `list` for an array). Source readers and the full cmdlet set are built on top of
> this spec.

## Goal

Cmdlets pass a single value down the pipe, and the comparison op consumes two of
those values. So that any cmdlet can follow any other — regardless of the source
data (Excel, CSV, SPSS, a database, …) — we use a **small, uniform, closed set of
value formats**. A generic cmdlet such as "select a field" therefore works
identically on a sheet, a table, a query result, etc.

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
| path | a filesystem path; two paths may be equal even when spelled differently (e.g. Windows `\` vs `/`, a UNC share vs a mapped drive) when they resolve to the same location |
| date/time | always timezone-aware, stored in UTC; naive datetimes are not allowed; the UI shows local time |
| categorical (single-punch) | carries the set of available options |
| categorical (multi-punch) | carries the list of available punches |

Every scalar type may additionally be **`sysmissing`** — the value is allowed to
be "missing" for any type (like `NULL` in a database column), not only for
types that are conventionally nullable.

## `sysmissing`

`sysmissing` is represented as Python **`None`** (like SQL `NULL` / JSON `null` →
`None`). `is_sysmissing(value)` is `value is None`.

`None` is deliberately distinct from *empty* values: an empty array (`[]`), an
empty block (`{}`), a nothing-punched multi-punch, an empty string (`""`), zero,
and `False` are all real values, and none of them equals `None`.

In comparison, `None` is undefined/uncertain:

- `eq`: `None` equals only `None`; `None` vs anything else → `false`.
- `ne`: `None` vs `None` → `false`; `None` vs anything else → `true`.
- ordering (`lt`, `le`, `gt`, `ge`) with `None` on either side → `false`.
- `contains` with `None` on either side → `false`.

## Compound types

Three compound types, which may nest (a field may itself be scalar or compound):

1. **block** — a collection of named fields. Each field has a name and a value
   of any scalar or compound type. Fields are selected by name (like
   `record.field["state"]`). Python representation: `dict`.

2. **named collection** — a block with a **fixed field order**, so fields can be
   selected by index **and** by name (Python `namedtuple` analog). Python
   representation: `dict` plus an explicit field-order list.

   > **Provisional — do not rely on it yet.** We are not yet sure this type
   > earns its place. A row read from a sheet is most naturally a *named
   > collection* (its fields have a fixed order), but an array's iterations must
   > be *blocks* — so a row would have to be either a block whose single field
   > is the named collection, or simply a block (in which case a named
   > collection is never needed). The provisional plan is to **avoid `named
   > collection` at the initial stage** and see whether blocks + arrays cover
   > the cases. If they do, we drop the type; if named collections prove to fit
   > better once readers and cmdlets are implemented, we promote them back and
   > update this spec.

3. **array** — a **block** repeated for each iteration. Each iteration:
   - is always a block of fields (an "array of ints" is **not** possible — to
     represent it you define a block with one integer field and an array of such
     blocks);
   - can be accessed by index;
   - can also be accessed by name when every iteration has a unique key (the
     record name in the collection). Every database record is assumed to have
     such a key.
   Python representation: `list` of blocks (plus an optional name→index map).

## Worked example: an Excel workbook

- The workbook is an **array of sheets**; each iteration (sheet) has both a name
  and an index.
- Each sheet is an **array of rows**; each iteration (row) has an index and a
  name (the name is read from an "index" column — see "Missing & duplicate
  names" for the fallback when it does not exist).
- Each row is a **block** whose fields are the sheet's columns (column names from
  row 1, made unique).
- `record.field["state"]` reads one field; there is no ambiguity from multiple
  "state" columns.

## Cmdlet naming

Names are shape-agnostic and mirror PowerShell, so they read the same whether the
array is a workbook, a sheet, a table, or a query result:

| PowerShell | Meaning | Cmdlet |
| --- | --- | --- |
| `Select-Object -ExpandProperty Name` | extract one field from every iteration → flat list | `select-property` |
| `Select-Object -Property A, B` | keep a subset of fields (narrower blocks) | `select-properties` |
| `Select-Object -First/-Last/-Skip/-Index` | pick specific iterations (by position or by name) | `select-item` |
| `Where-Object { … }` | filter iterations by a condition | `where` |
| `ForEach-Object { … }` | map/transform each iteration | `map` |
| `Sort-Object [-Property X]` | order iterations (optionally by a field) | `sort` |

## Shape-changing operations

On an **array**:

- `where` (filter iterations) → an array again, same field shape.
- `select-item` (pick one iteration, by name or by position) → a **block** (one
  field per column).
- `select-properties` (filter fields) → an array again, smaller field shape.
- `select-property` (extract one field) → a flat list of that field's values
  (this is what `… | select-property "B" | count` uses).
- `sort` (reorder iterations) → an array again, same field shape. `args.by`
  (optional) sorts blocks by a field; without it an array of scalars sorts
  naturally. `args.descending: true` reverses the order.

## Comparison semantics

`op` compares two values and returns `true`/`false` (never an error for a
*false comparison*). Coercion is minimal:

- `bool` is its own type: `False` ≠ `0`, `True` ≠ `1`, `False` ≠ `0.0`; a `bool`
  is never ordered against, or contained in, a non-`bool`.
- numbers unify: `1 == 1.0` → `true`.
- a numeric string coerces to a number: `"0" == 0` → `true`, `"3.14" == 3.14` →
  `true` (and likewise for ordering), because Excel/pandas auto-detection makes
  this hard to avoid.
- a non-numeric string vs a number → `false`.
- text vs text: exact (`eq`/`ne`), lexicographic (`lt`/`le`/`gt`/`ge`), substring
  (`contains`).
- date/time vs date/time: chronological (timezone-aware). A calendar date and a
  full timestamp are not directly comparable (Python raises); a naive datetime is
  invalid per "Dates & time".

Net effect: `0 == false` → `false`, while `"0" == 0` → `true`.

### Compound comparison (`eq` / `ne`)

`eq` and `ne` also compare compound values **deeply**: the comparison recurses
into fields/iterations and re-applies the scalar rules above to each leaf. Two
compound values of different kinds are never equal (a block ≠ an array ≠ a
scalar).

- **block vs block** — equal iff they have the same set of field names **and**
  each field's value compares equal by name. Field order does **not** matter:
  `{ Name, FullName }` equals `{ FullName, Name }`.
- **array vs array** — equal iff they have the same length and each iteration
  compares equal **in position order**. The same iterations at different
  positions are **not** equal by default.

`lt`/`le`/`gt`/`ge` stay **scalar-only**: ordering has no meaning for a compound
value, so a compound value on either side returns `false` (they never recurse).
`contains` keeps its membership semantics (substring for text, membership for
arrays) and does not deep-compare.

### Order-agnostic arrays

Two arrays that contain the same iterations in a different order (e.g. two
workbooks listing the same US states, one alphabetically, one by zip) can be
compared as equal **sets** — strictly, as *multisets* (duplicates still matter).
Array equality is strict-order by default; order-agnostic comparison is opt-in,
spelled in either of two equivalent ways:

- **an argument on the comparison** — `eq`/`ne` accept
  `args: { unordered_arrays: true }`, stored on the rule as
  `op_args: { unordered_arrays: true }`; or
- **a dedicated op** — `eq-unordered`, which is `eq` with
  `unordered_arrays: true` hard-wired.

The flag is recursive (nested arrays inside blocks are also compared
order-agnostically) and has no effect on blocks or scalars. A `sort` cmdlet is
also available for the related but different job of *canonicalizing* an array's
order before a strict comparison (see "Shape-changing operations").

## Missing & duplicate names

- **Column with no header** → use the source's native coordinate: Excel letters
  (`"A"`, `"B"`, …), CSV/DB positions (`"1"`, `"2"`, …).
- **Row with no index column** → generate a 1-based integer counter as the
  provisional name.
- **Non-unique column names** → never drop or overwrite; deduplicate in order.
  First occurrence keeps the name, later duplicates get a numeric suffix:
  `state`, `state.1`, `state.2`, … (pandas' default `mangle_dupe_cols`
  behaviour; the underscore form `state_2` is the alternative). This happens at
  the source reader, producing unique field names in the block.

## Representation (Python / JSON / DB / UI)

- **Python**: scalar → native (`str`, `int`, `float`, `bool`, `datetime`, `date`);
  `sysmissing` → `None`; block → `dict`; named collection → `dict` + field order;
  array → `list` of blocks (+ optional name→index map); categorical → value object
  carrying `value` + `options` (to define when categoricals are implemented).
- **JSON / DB / UI**: scalars → JSON primitives; date/time → ISO-8601 (UTC);
  `sysmissing` → `null`; block → object; array → array; categorical → `{ value,
  options }` (future).

## Dates & time

Date/time values are always timezone-aware and stored in UTC; **naive datetimes
are not allowed**. The frontend displays them in the browser's local timezone
(`new Date(isoString)` already converts).

## Remaining to implement

- Typed value objects for categoricals and the block / named collection / array
  wrappers (until then, the plain-Python rules above apply).
- Source readers (`get-content` for Excel/CSV/SPSS/DB, …) and the full cmdlet set
  (`select-property`, `select-properties`, `select-item`, `where`, `map`,
  `to-string`, …).

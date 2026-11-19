# Commands

APQA rules are built by piping small commands together — each command does one
job (read a file, pick a field, count something, check something). For example:

```
get-content Specs.xlsx | select-field "Title Details" | select-field "B" | count
```

This page lists every command you can use, grouped by what it does. For the
precise rules of how values are stored and compared, see the
[cmdlet data formats](docs/cmdlet-data-formats.md) guide.

## Reading data

Commands that bring your data into the rule — the first command in a chain.

- **`get-content-text`** — read a plain text file as a single piece of text.
  Needs a `path` (and optionally an `encoding`, default UTF-8).
- **`get-content`** — the same reader under its shorter name; use it to read a
  text file.
- **`get-content-excel`** — read an Excel workbook; every sheet becomes a block
  you can then pick fields from. Needs a `path`.
- **`get-content-mdd`** — read an MDD metadata document (IBM SPSS Data
  Collection). Needs a `path`. Windows only.
- **`get-content-msmarkitdown`** — convert a file (Word, PDF, Excel, …) into
  readable Markdown text. Needs a `path`.
- **`get-filesystem-obj-info`** — describe a file or folder (type, size, dates).
  Needs a `path`.
- **`get-content-mrs-preprocessor`** — run a small C-style preprocessor over a
  file and return its `#define` definitions as a block. Needs a `path`; you can
  also set the `#include` root (`current_dir`) and make matching
  case-insensitive.
- **`get-content-network-fetch`** — download a web address and return its status
  code, body text, and headers. The address comes from the previous command.

### Define constants

- **`literal`** — a fixed value (a number, text, true/false, a path, a date, or
  a list) you type directly into a rule.
- **`literal-from-json`** — build a value from a JSON string you type in.

## Transformations/modifications (`transform-*`)

- **`transform-strip-html`** — remove HTML tags, leaving just the readable text.
- **`transform-text-regex`** — find-and-replace in text using a pattern (with
  optional case-insensitivity and a replace limit).
- **`transform-text-code-grab-assignments-mrs`** — pull out the values of
  `NAME = VALUE` assignments from a text (for example from a script file). Give
  it the `variable_name` to look for.
- **`transform-text-count-chars`** — number of characters in a text (optionally
  strip surrounding whitespace first).

## Checking values (`validate-*`)

- **`validate-xml-compatible`** — check the text can be placed into an XML
  document unchanged (no unescaped `&` or broken tags).
- **`validate-text-matches`** — check every text value contains/matches a
  pattern.
- **`validate-network-request-result`** — check a downloaded page's status is
  "OK" (2xx).

## Unary (`is-*`)

- **`is-sysmissing`** — is the value missing?

## Picking & rearranging & changing shape (`select-*`, `foreach-*`, `sort`, `exclude-*`, `include-*`)

- **`select-field`** — pick one field from a block, or pull that field out of
  every row into a list.
- **`select-item`** — pick one item from a list by its position.
- **`select-range`** — take a slice of a list (from a start position up to an
  end position).
- **`foreach-item`** — run a command on every item of a list.
- **`foreach-field`** — run a command on every field of a block.
- **`foreach-deep-node`** — run a command on every single value inside a nested
  structure.
- **`sort`** — reorder a list, optionally by a field.
- **`exclude-child`** — drop the direct children whose path matches a rule.
- **`exclude-deep-node`** — drop every part whose path matches a rule.
- **`include-child`** — keep only the direct children whose path matches a rule.
- **`include-deep-node`** — keep only the parts whose path matches a rule.
- **`count`** — how many entries there are (rows in a list, fields in a block;
  a missing value counts as zero).

## Type conversion (`as-*`)

- **`as-text`** — to text.
- **`as-integer`** — to a whole number.
- **`as-real`** — to a decimal number.
- **`as-boolean`** — to true/false.
- **`as-path`** — to a path.
- **`as-date`** — to a date/time. Give it a `tz` (time zone) for dates that
  don't carry one.

## Logical, combining true/false (`logical-*`)

- **`logical-not`** — flip a true/false value.
- **`logical-and`** / **`logical-or`** — combine several commands with AND / OR.
- **`logical-any`** / **`logical-all`** — "is any value true?" / "are all values
  true?" over every value inside a structure.
- **`logical-tristate-*`** (`not` / `and` / `or` / `any` / `all`) — the same,
  but treating a missing value as "unknown" rather than false.

## Bit-by-bit math (`bitwise-*`)

- **`bitwise-not`** — flip every bit of a whole number.
- **`bitwise-and`** / **`bitwise-or`** / **`bitwise-xor`** — combine whole
  numbers bit by bit.
- **`bitwise-lshift`** / **`bitwise-rshift`** — shift the bits of a whole number
  left / right.

## Comparing the two sides (`cmp-*`)

These are not commands you pipe — they are the **comparison** between the left
and right side of a rule.

- **`cmp-eq`** — equal.
- **`cmp-ne`** — not equal.
- **`cmp-eq-unordered`** — equal, ignoring the order of lists.
- **`cmp-contains`** — contains (a piece of text, or a member of a list).
- **`cmp-lt`** / **`cmp-le`** / **`cmp-gt`** / **`cmp-ge`** — less than /
  less than or equal / greater than / greater than or equal.

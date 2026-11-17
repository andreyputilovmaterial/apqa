# QC results: reporting where a rule failed

> Status: **implemented.** This document specifies how APQA reports *where* a QC
> rule failed during the **run QC tests** stage, so a user can go straight to the
> offending component, field, or iteration. It covers two mechanisms:
> **chain-step error context** (for errors that raise) and **diagnostic notes
> with data paths** (for rules that run but compare to `False`).

## The problem

A QC/QA tool must be *informative*: when a rule does not pass, the output should
point at the places that need attention — which component, which field, during
which iteration — not just print `result: False`.

A rule run has **two different kinds of bad outcome**, and they need different
machinery:

| Kind | What happens | Where the "why" lives |
| --- | --- | --- |
| **Error** | a cmdlet cannot do its work (missing field, unreadable file, unknown cmdlet, missing optional dependency) and raises | in the exception |
| **Validation failure** | the rule *runs* but the comparison returns `False` | nowhere — `False` is a value, and the detail was already collapsed to a boolean |

The two must not be conflated. A false comparison is a *result*, not an error:
`cmp-eq` returning `False` is a normal pipe value consumed by `cmp-ne`,
`logical-not`, `where`, and friends. So the detail for a `False` result cannot be
carried by an exception — it must be carried **alongside** the value, through a
separate channel.

### Worked example

A rule `get-content-mdd | validate-xml-compatible  cmp-eq  literal(True)`:

- If the MDD path is wrong or the COM read fails, `get-content-mdd` *raises* →
  an **error**, reported with chain-step context.
- If the MDD reads fine but some label is not XML-compatible,
  `validate-xml-compatible` returns `False` → a **validation failure**, and the
  only useful information is *which field, in which section, held what text*.

## Two mechanisms

### 1. Chain-step error context (`ChainError`)

`src/cmdlets/chain_runner.py` wraps every cmdlet call so a failure carries its
position in the chain:

```python
class ChainError(Exception):
    def __init__(self, cmdlet, step, args, message):
        self.cmdlet = cmdlet
        self.step = step
        self.args = args
        super().__init__(message)
```

`run_chain` catches the original exception and re-raises:

```python
raise ChainError(
    cmdlet=name, step=index, args=args,
    message=f'cmdlet {name!r} (step {index}): {error}',
) from error
```

The `from error` preserves the original exception as `__cause__`, so the full
cause chain stays available to pytest and the HTTP endpoint. An unknown cmdlet is
also wrapped (`cmdlet 'nope' (step 0): cmdlet not found: nope`), while a missing
comparison op still raises a plain `KeyError` (it is not a chain step).

Example: a rule whose `get-content-excel` step has no `openpyxl` raises

```
ChainError: cmdlet 'get-content-excel' (step 0): get-content-excel: missing optional dependency 'openpyxl'
```

with `__cause__` being the original `ImportError`.

### 2. Diagnostic notes with data paths (`src/cmdlets/diagnostic.py`)

For a `False` result there is no exception, so cmdlets that know *where* a value
failed record a **note**. A note is a small JSON-safe mapping:

```json
{"path": ["Fields", "BrandAwareness", "Label"], "message": "not XML-compatible: …"}
```

`path` is the **data path** — the sequence of block keys and array indices that
leads from the top-level piped value to the offending leaf. It is the "which
component, which field, during which iteration" answer:

- `Fields.BrandAwareness.Label` — field → subfield → leaf;
- `Pages.Q1.value[2].Categories['None of the above'].Label` — section → page →
  iteration → categories → category → leaf.

Notes are collected per rule run in a `Notes` instance held in a
`contextvars.ContextVar`, so:

- a cmdlet records a note by calling `record_note(path, message)` with **no
  signature change** (the note sink is ambient, like a logger), and
- concurrent rule runs (the webserver is multithreaded) never mix notes.

The runner opens a fresh `Notes` for each run:

```python
# src/rule_runner.py
def run_rule_with_report(rule):
    left, right, op, op_args = _parse_rule(rule)
    with collect_notes() as notes:
        left_value = run_chain(left)
        right_value = run_chain(right)
        result = comparisons.get(op)(left_value, right_value, op_args)
    return result, notes.items
```

`run_rule(rule)` is now a thin wrapper that delegates to `run_rule_with_report`
and discards the notes, so `Rule.run()` keeps returning a plain `True`/`False`
and existing callers are unaffected.

### A validator opts in

`validate-xml-compatible` still returns a plain `bool` (so the rule that compares
it to `literal(True)` keeps working), but while it walks the block/array it
records a note per failing text leaf, threading the path as it goes:

```python
def validate_xml_compatible(value, args):
    ...
    return _check(value, [], current_notes())

def _check(value, path, notes):
    if isinstance(value, str):
        problem = _xml_problem(value)
        if problem is not None:
            if notes is not None:
                notes.note(path, f'not XML-compatible: {problem} (value: {_clip(value)!r})')
            return False
        return True
    if isinstance(value, dict):
        return all(_check(v, path + [key], notes) for key, v in value.items())
    if isinstance(value, list):
        return all(_check(v, path + [index], notes) for index, v in enumerate(value))
    return True
```

`current_notes()` returns `None` when the cmdlet is called directly (outside a
run), so the cmdlet's behavior is unchanged in unit tests.

`validate-text-matches` opts in the same way: it walks the piped value, matches
each `text` leaf against its `pattern`, and records a note whose path points at
the leaf that failed (e.g. `Fields.BrandAwareness.Label`). The wording of its
note is `text does not match <pattern> (value: <clip>)`.

## How the failure reaches the user

### "Run QC tests" mode (pytest)

`tstsuite.run_tst_case` runs the rule with the report and builds a rich
`AssertionError`:

```python
result, notes = run_rule_with_report(rule)
if result is not True:
    details = format_notes(notes)
    message = f'QC rule failed: {rule.name} [{rule.id}] (result: {result})'
    if details:
        message = f'{message}\n{details}'
    raise AssertionError(message)
```

So a failed `Verify all xml` rule now prints:

```
QC rule failed: Verify all xml [verify-all-xml] (result: False)
- Fields.BrandAwareness.Label: not XML-compatible: not well-formed (invalid token): line 1, column 13 (value: 'aware & <b>')
```

The rule **id** and **name** are both present, and the note points at the exact
field. An error (not a `False`) instead surfaces as a pytest ERROR with the
`ChainError` message and the chained cause.

### `POST /functionality/run-rule`

The endpoint prefers `run_rule_with_report` when the config provides it and
returns the notes to the frontend:

```json
{"result": false, "notes": [{"path": ["Fields", "A", "Label"], "message": "…"}]}
```

When there are no notes (or the config only provides `run_rule`), the response
stays `{"result": <bool>}` with no `notes` key, preserving the previous contract.

## Data-path rendering (`format_path`)

`format_path` renders a path as a short, human-readable address:

- a key that is a plain identifier joins with `.` — `Fields.BrandAwareness.Label`;
- an array index becomes `[i]` — `Pages.Q1.value[2]`;
- a key that is not a plain identifier is quoted — `Categories['None of the above']`.

Examples:

| path | rendered |
| --- | --- |
| `['Fields', 'BrandAwareness', 'Label']` | `Fields.BrandAwareness.Label` |
| `['Pages', 'Q1', 'value', 2]` | `Pages.Q1.value[2]` |
| `['Pages', 'Q1', 'value', 2, 'Categories', 'None of the above', 'Label']` | `Pages.Q1.value[2].Categories['None of the above'].Label` |

## Authoring guidance for cmdlet authors

- **Errors raise.** When a cmdlet physically cannot do its work, raise a normal
  exception with a readable message; `run_chain` adds the step context and
  preserves the cause chain automatically. Do not catch and convert to `False`.
- **Validation failures return `False` and record a note.** A terminal validator
  that walks a compound value should thread the path and call
  `record_note(path, message)` (guarding against `current_notes()` being `None`).
- **Keep notes JSON-safe.** A note is `{path: [str|int, …], message: str}`. Put
  any offending value into the *message* (clipped), not into the path.
- **The notes channel is opt-in.** Most cmdlets (readers, processors, `count`,
  `sort`, …) record nothing; only validators (and, in the future, comparison
  ops) do.

## Relationship to other design notes

- The earlier rule — "a normal Python exception is all we need" (historical
  `design-notes.md`) — is still true for *errors*, but a `False` comparison is not
  an exception, which is exactly why the notes channel exists.
- `docs/roadmap.md` tracks an **error value type** and a `try-catch` cmdlet (an
  in-band way to turn a failure into a value that can be caught). The notes
  channel is orthogonal and smaller: it attaches *where* information to a result
  without changing the value that flows through the pipe.

## Future extensions

- **Comparison diffs.** `cmp-eq` recurses field-by-field and returns `False` at
  the first difference; it can record the same kind of note (`path` = the
  differing field) so a "stubs in A == stubs in B" rule reports the exact
  differing stub.
- **Iteration context in `map`/`where`.** A nested chain failure inside a
  per-iteration predicate/transform can wrap its `run_chain` call with "iteration
  N" so the note/error names the iteration as well as the field.
- **Notes on the rule card.** The frontend currently renders only `{result}`; it
  can render `notes` as the list of problems the validator found.


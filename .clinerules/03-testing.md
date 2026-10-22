# Testing

There are two distinct uses of pytest — do not conflate them:

1. **Development tests** (verify program functionality). These live in `tests/` and are **not** included in the final bundle.
2. **"Run QC tests" mode** (the product feature). The final bundle contains a **single discoverable parametrized entry point** (appended by `build.sh`) that reads rules from the DB file. There is **no physical test discovery** — one entry point parametrized from the database.

- The QC-rules DB file is passed via env var `APQA_DB_FILE` (set by the caller `.sh`/`.bat` script). User CLI params are not available in this mode.
- `--import-mode=importlib` is required **only when running the bundle with pytest** (pinliner limitation). Do **not** add it to development tests — it is unnecessary there.
- The QC rules stored in the project DB YAML are the fixtures and acceptance criteria.
- `tests-real-sensitive-data/` is gitignored (sensitive/proprietary data). Never commit it.

## Why pytest / is it permanent?

The **function** we need is minimal: run each rule and return zero/non-zero exit
status plus which rules failed — doable without pytest.

pytest is a pragmatic *starting point*, not a hardcoded decision: it is the
standard, widely supported test environment (and the only one the author knows
well), and it brings pass/fail marks, the `pytest-html` report plugin, and a large
tooling ecosystem.

Known downsides (both accepted, both contained):

1. It may be an unnecessary dependency — pytest machinery is more than the
   zero/non-zero exit status we strictly need.
2. It muddies the word "tests": "run QC rules" runs the *program* (not *tests the
   program*), which is easy to confuse with development tests.

Why the confusion is contained: the bundle is distributed **without** `tests/`, and
the run-QC-rules entry point is **appended by `build.sh`**, so it exists only in the
final bundle, never in the source tree.

The author may migrate away from pytest if a concrete reason appears.

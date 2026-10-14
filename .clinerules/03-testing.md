# Testing

There are two distinct uses of pytest — do not conflate them:

1. **Development tests** (verify program functionality). These live in `tests/` and are **not** included in the final bundle.
2. **"Run QC tests" mode** (the product feature). The final bundle contains a **single discoverable parametrized entry point** (appended by `build.sh`) that reads rules from the DB file. There is **no physical test discovery** — one entry point parametrized from the database.

- The QC-rules DB file is passed via env var `APQA_DB_FILE` (set by the caller `.sh`/`.bat` script). User CLI params are not available in this mode.
- `--import-mode=importlib` is required **only when running the bundle with pytest** (pinliner limitation). Do **not** add it to development tests — it is unnecessary there.
- The QC rules stored in the project DB YAML are the fixtures and acceptance criteria.
- `tests-real-sensitive-data/` is gitignored (sensitive/proprietary data). Never commit it.

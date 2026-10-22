# Project context

> Living document. Updated after every task. Read this first at the start of every task.

## Last state

- Documentation pass: rewrote `README.md` (user-facing), wrote the in-app help
  `help.md`, and added a developer/architecture guide `docs/development.md`
  (linked from the README). Clarified the pytest rationale in
  `.clinerules/03-testing.md`.
- `help.md` is the **in-app user help** — embedded by `build.sh` into
  `src/GENERATED/HELP.py` and rendered on the `/help` page. Keep it user-facing,
  never developer-facing.
- Archived the original `project-description.md` to `docs/design-notes.md`
  (historical design notes, superseded by `docs/development.md`).
- `main` is 2 commits ahead of `origin/main` (not pushed). Previous state included
  the QC-rules DB schema work + the qcrule CRUD endpoint
  (`src/frontend/endpoints_rule_crud.py` + tests) and the project-context workflow.

## Repo overview

- **APQA** — a quality-control (QC) rules engine: define/manage rules, then run them
  as tests.
- Two run modes: (1) desktop app (`--program ui --db-file <path>`) to edit rules,
  (2) run QC rules via `pytest`
  (`APQA_DB_FILE=<path> … -m pytest --import-mode=importlib apqa_bundle.py`).
- Bundled with `pinliner` into a single self-contained `dist/apqa_bundle.py` via
  `build.sh`.
- UI is Vue but written as plain `.js`/`.css` (no `.vue`/`.ts`).
- QC rules live in a DB (YAML) and are the fixtures/acceptance criteria.

## Key conventions / gotchas

- Only **relative imports** in `.py`; imported-module paths need `__init__.py` at
  each level (`src/launcher.py` is the only import exception).
- No runtime dependency on separate local files (no `.env`, no standalone JS/CSS);
  runtime content is embedded via `GENERATED/` folders.
- `--import-mode=importlib` only when running the bundle under pytest (not dev tests).
- `tests-real-sensitive-data/` is gitignored — never commit it.
- pytest for "run QC rules" is a pragmatic starting point, not a hardcoded decision
  (see `.clinerules/03-testing.md` and `docs/development.md`).

## Open questions / TODO

- Compound scalar types (object with named fields, collection, tuple) still being
  finalized.


# Project context

> Living document. Updated after every task. Read this first at the start of every task.

## Last state

- Initialized the project-context workflow: added `.clinerules/00-project-context.md`
  (rule to read/update this file on every task) and mentioned it in `README.md`.

## Repo overview

- **APQA** — a quality-control (QC) rules engine.
- Bundled with `pinliner` into a single self-contained `dist/apqa_bundle.py` via `build.sh`.
- UI is Vue but written as plain `.js`/`.css` (no `.vue`/`.ts`).
- QC rules live in a DB (YAML) and are the fixtures/acceptance criteria.

## Key conventions / gotchas

- Only **relative imports** in `.py`; imported-module paths need `__init__.py` at each level.
- No runtime dependency on separate local files (no `.env`, no standalone JS/CSS).
- `--import-mode=importlib` only when running the bundle under pytest (not dev tests).
- `tests-real-sensitive-data/` is gitignored — never commit it.

## Open questions / TODO

- None recorded yet.

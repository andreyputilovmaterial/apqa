# Project context

> Living document. Updated after every task. Read this first at the start of every task.

## Last state

- Consolidated `dev-working-cline` back into `main` (fast-forward, both at `e6ba3d6`).
  `main` is now **2 commits ahead of `origin/main`** and not yet pushed.
- `main` now includes the QC-rules DB schema work and the qcrule CRUD endpoint
  (`src/frontend/endpoints_rule_crud.py` + tests), plus the project-context workflow
  (`docs/project-context.md`, `.clinerules/00-project-context.md`).
- Untracked, not yet committed: `.clinerules/08-commit-messages.md`.

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

# Project context

> Living document. Updated after every task. Read this first at the start of every task.

## Last state

- Added a **SQLite rules database backend** (`src/db_processors/sqlite.py`,
  type `'sqlite'`), in parallel with the existing YAML backend. SQLite is now the
  documented default; the format is selected purely by file extension via
  `detect_type` — `.sqlite3`/`.sqlite` → `sqlite`, `.yaml`/`.yml` → `yaml`. There
  is still no fallback/"default" resolution: the path is always passed explicitly
  (CLI `--db-file` or `APQA_DB_FILE`).
- SQLite schema: one row per rule — `name` (PK), `meta`/`"left"`/`"right"` as JSON
  text, `op` as text. `"left"`/`"right"` are double-quoted (SQL keywords). The
  backend is thread-safe (`ThreadingHTTPServer`) via `threading.RLock` +
  `sqlite3.connect(..., check_same_thread=False)`, and is write-through (`save()`
  just commits).
- SQLite **requires the file to exist** (same as YAML) and raises
  `FileNotFoundError` otherwise; the schema is auto-created on first open of an
  empty file (`CREATE TABLE IF NOT EXISTS`). So a new project = `touch x.sqlite3`.
- Fixed a latent bug this exposed: `tstsuite.load_cases()` reads `dbfile.rules`,
  but that accessor only existed on the YAML backend. Moved the generic `.rules`
  property up to `DBFile` (base) and removed the duplicate from `yaml.py`.
- Updated `README.md`, `help.md`, `docs/development.md` (new "Rules database
  storage" subsection) and the example `run_*.sh`/`.bat` scripts to lead with
  `.sqlite3`.
- Tests: 397 passed (added `tests/test_db_processors_sqlite_crud.py`, 18 tests).
  Verified end-to-end that the built `dist/apqa_bundle.py` dispatches `.sqlite3`
  (collects `test_run_case[case0]` under pytest).

## Repo overview

- **APQA** — a quality-control (QC) rules engine: define/manage rules, then run them
  as tests.
- Two run modes: (1) desktop app (`--program ui --db-file <path>`) to edit rules,
  (2) run QC rules via `pytest`
  (`APQA_DB_FILE=<path> … -m pytest --import-mode=importlib apqa_bundle.py`).
- Bundled with `pinliner` into a single self-contained `dist/apqa_bundle.py` via
  `build.sh`.
- UI is Vue but written as plain `.js`/`.css` (no `.vue`/`.ts`).
- QC rules live in a DB (SQLite by default; YAML also supported) and are the
  fixtures/acceptance criteria. Storage backends register in
  `src/db_processors/dbfile_base.py` and are selected by extension in
  `detect_type.py`.

## Key conventions / gotchas

- Only **relative imports** in `.py`; imported-module paths need `__init__.py` at
  each level (`src/launcher.py` is the only import exception).
- No runtime dependency on separate local files (no `.env`, no standalone JS/CSS);
  runtime content is embedded via `GENERATED/` folders.
- `--import-mode=importlib` only when running the bundle under pytest (not dev tests).
- `tests-real-sensitive-data/` is gitignored — never commit it.
- pytest for "run QC rules" is a pragmatic starting point, not a hardcoded decision
  (see `.clinerules/03-testing.md` and `docs/development.md`).
- New storage backends must implement the full CRUD contract in
  `dbfile_base.py` **and** be imported in `db_processors/__init__.py` (import = the
  `@DBFile.register(...)` side effect). Generic accessors like `.rules` belong on
  the base class, not per-backend.

## Open questions / TODO

- Compound scalar types (object with named fields, collection, tuple) still being
  finalized.
- SQLite is the "default" only by convention (docs/examples); there is no fallback.
  Decide whether SQLite should auto-create a missing file instead of requiring it
  to exist (currently it matches YAML's fail-early behavior).
- `.db` extension is intentionally **not** mapped to SQLite (ambiguous); add it
  only if a concrete need appears.


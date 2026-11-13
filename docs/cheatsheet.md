# APQA — cheatsheet

Quick reference for the commands used most often. Run from the repo root unless
stated otherwise.

## Build & run the app

```bash
./build.sh       # build the self-contained program -> dist/apqa_bundle.py
./run_ui.sh      # open the desktop app (QC-rule editor) in the browser
./run_tests.sh   # build, then run all QC rules as tests (pytest on the bundle)
```

The `run_*.sh` scripts prepare the venv first (via `run_init.sh`) and point at
the sample DB `tests-real-sensitive-data/projects.sqlite3`. Edit the `DBFILE`
line (or pass your own path) to pick another project.

## Dev backend (`dev_backend.py`)

The backend must stay on `localhost:5280` (the Vite dev server hard-codes that
proxy target). Manage it only via this script — never `lsof`/`kill`/`sudo`.

```bash
python dev_backend.py status    # running & healthy?  (exit 0 = healthy)
python dev_backend.py start     # start headless on 5280 if not already running
python dev_backend.py stop      # stop it (idempotent)
python dev_backend.py restart   # stop + start + wait for health
python dev_backend.py health    # HTTP probe of http://localhost:5280/
python dev_backend.py logs      # tail .dev_backend.log (default: last 50 lines)
```

Flags: `--db-file PATH` (default `tests-real-sensitive-data/projects.sqlite3`),
`--port N` (default 5280), `--json` (status/health), `--lines N` (logs).

## Development tests

```bash
./.venv/bin/python -m pytest tests/                     # full Python suite
./.venv/bin/python -m pytest tests/test_dev_backend.py  # one file
```

## Frontend dev server (Vite, needs Node)

```bash
cd src/frontend/app_js
npm install
npm run dev        # hot-reload UI; proxies API calls to http://localhost:5280
npm run test:unit  # Vitest unit tests
```

## UI program flags

Passed via `./.venv/bin/python -m src.launcher --program ui ...` (what `run_ui.sh`
does) or `dev_backend.py start`.

- `--db-file PATH` — rules database (`.sqlite3`/`.sqlite`, or `.yaml`/`.yml`).
- `--browser MODE` — `launch-system-default-browser` (default), `no-op`
  (headless), or `pywebview` (not implemented — fails early).
- `--config-webserver-port PORT` — fixed port (fails if occupied); `PORT+`
  auto-increments from `PORT`; omit for the default auto-increment from 5280.

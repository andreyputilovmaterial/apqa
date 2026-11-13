---
name: backend
description: Manage the local APQA dev backend on localhost:5280 — status, start, stop, restart, health, logs via dev_backend.py (never lsof/kill/sudo).
---

# Manage the APQA dev backend

The backend is the Python web server that serves the app UI and its `/qc`,
`/functionality`, `/assets`, … endpoints. Vite proxies to it at
`http://localhost:5280`, so the backend must stay on port 5280 during frontend work.

## Always

- Run from the repo root.
- Use `python dev_backend.py <verb>` (the venv is resolved by the script itself).
- Never use `lsof`, `kill`, `sudo`, or `taskkill` directly.

## Verbs

- `status`  — is it running and healthy? (exit 0 = running/healthy)
- `start`   — start on 5280 if not already running (headless, no browser)
- `stop`    — stop it (idempotent)
- `restart` — stop + start + wait for health
- `health`  — HTTP probe of `http://localhost:5280/` (exit 0 = HTTP 200)
- `logs`    — tail the backend log `.dev_backend.log`

## Output

- Success messages (backend started/stopped/healthy/running) print **green**; the
  key failure message prints **red**. Colors appear only on an interactive
  terminal (stdout is a TTY) and are suppressed when output is piped or `NO_COLOR`
  is set.

## Example

    python dev_backend.py restart --db-file tests-real-sensitive-data/projects.sqlite3
    python dev_backend.py health

If `start`/`restart` reports the backend did not become healthy, read
`python dev_backend.py logs` for the startup error before changing anything else.

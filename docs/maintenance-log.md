# Maintenance log

> Cross-project maintenance notes. Entries here capture **structural** changes
> that apply to any project sharing this repo's shape — a `launcher` used as the
> key router (`--program <name>`), and `pinliner` producing a one-file bundle.
>
> Repo-specific changes do **not** belong here; they stay in the commit history
> and `docs/project-context.md`. Anything recorded here is meant to be repeatable
> in other projects of the same structure.
>
> Entries are ordered **newest first**.

## How to read an entry

Each entry is a section whose heading reads like a commit subject: it states the
**intent** of the change and **where** the change happens (component/module).
Inside, answer the questions needed to repeat the same update elsewhere:

- **When** — date/time requested and implemented.
- **What & why** — the request and the reasoning behind the chosen approach.
- **Input** — a sample of the code/file **before** the change.
- **Output** — a sample of the code/file **after** the change.
- **Repeat** — a checklist of the exact steps to apply the same convention in
  another project.

Two concepts are easy to conflate, so they are spelled out separately:

- **Invocation modes** — the ways to *start* the program:
  1. from the **bundle** (`python apqa_bundle.py --program X`),
  2. through the **launcher** (`python -m src.launcher --program X`),
  3. **directly** at a starter module (`python -m src.main_ui_program …`).
- **Import selection** — how an entry-point module's `import` statements branch
  on the import context (package vs flat), set by Python via `__package__`. It
  is **not** a 1:1 map of the invocation modes.

---

## UI: `--config-webserver-port` — fixed / auto-increment / default port

- **Requested:** 2026-11-13
- **Implemented:** 2026-11-13
- **Where:** `src/webserver_config.py` (new), `src/main_ui_program.py` (flag +
  wiring), `dev_backend.py` (pins the port), `tests/test_webserver_config.py`.

### What & why

The backend port was always `5180` then auto-incremented (`find_free_port`), so
it silently drifted off the Vite proxy port when 5180 was taken. The new
`--config-webserver-port` flag selects between: a **fixed** port (fail if
occupied), an **auto-incrementing** port (`<port>+`), and the **default**
auto-increment-from-5180. `dev_backend.py` passes the fixed `5180` form so the
backend never drifts off Vite's hard-coded `localhost:5180`. The Vite note is
recorded in code comments and `--help` (dev server hard-codes 5180; without it
any port works equally well).

### Repeat

1. Keep port-picking logic in a small non-entry-point module (testable without
   importing the UI program).
2. Reuse the existing `find_free_port` for auto-increment; add an explicit
   free-port probe for the fixed case that raises a readable error.
3. Document the three flag forms in the module docstring, `--help`, and the
   architecture guide, including the Vite `localhost:5180` note.

---

## Dev backend tooling: a cross-platform `dev_backend.py` + a `--browser` launch mode

- **Requested:** 2026-11-13 (agent- and human-manageable backend restarts on localhost:5180)
- **Implemented:** 2026-11-13
- **Where:** repo root (`dev_backend.py`), `src/browser_launcher.py` +
  `src/main_ui_program.py` (new `--browser` flag), `.clinerules/skills/backend/`,
  `.clinerules/30-dev-backend-tooling.md`, `.gitignore`, `tests/test_browser_launcher.py`,
  `tests/test_dev_backend.py`.

### Problem

The desktop app is a Python backend + browser UI. The backend starts on
`localhost`, default port 5180, but `find_free_port` **silently increments** the
port when 5180 is taken (`src/main_ui_program.py` → `find_free_port.py`), while
the Vite dev server hard-codes `http://localhost:5180` as its proxy target.
There was no idempotent way to check/start/stop/restart the backend, no health
check, and no record of which process to kill — so an agent (or a human)
resorted to platform-specific `lsof`/`sudo`/`kill` guessing, sometimes killed
the wrong process, and "start" could appear to succeed on the wrong port.

### Intent

One deterministic, cross-platform control point for the dev backend, usable by
both humans and agents: `status` / `start` / `stop` / `restart` / `health` /
`logs`. Plus a `--browser` flag on the UI program so automation can start the
server without popping a browser.

### Reasoning

- The tool is **Python** (already a hard app requirement), so it is identical on
  Windows/macOS/Linux — no `.sh`+`.bat` pair, and no `lsof`/`sudo` on the happy path.
- A **pid file** is the authoritative record of what `start` spawned (fully
  portable); an OS-specific port→PID lookup is only a *fallback* for a backend
  started outside the tool (e.g. the debugger).
- `start` is idempotent and headless; the agent is pointed at the script via a
  **Cline skill** (on-demand procedure) plus a one-line **rule** (always-on
  pointer), so it stops improvising `lsof`/`kill`.
- The browser-launch decision is extracted to `src/browser_launcher.py` so the
  three modes are testable without importing the heavy UI entry-point module
  (and its `GENERATED/` + `.env` dependencies).

### Proposed plan (as implemented)

1. `src/browser_launcher.py` — `launch_browser_for_mode(mode, url)` with modes
   `launch-system-default-browser` (default), `no-op`, and `pywebview` (raises
   `NotImplementedError`).
2. `src/main_ui_program.py` — add `--browser` (choices above, default
   `launch-system-default-browser`); validate `pywebview` early (fail before the
   server starts); call `launch_browser_for_mode` instead of `launch_browser`.
3. `dev_backend.py` — the subcommands above; pid file + port→PID fallback;
   HTTP 200 health probe; headless start (`--browser no-op`); output to
   `.dev_backend.log`.
4. `.gitignore` — ignore `.dev_backend.pid` and `.dev_backend.log`.
5. `.clinerules/skills/backend/SKILL.md` + `.clinerules/30-dev-backend-tooling.md`
   — tell the agent to use `dev_backend.py` and never `lsof`/`kill`/`sudo`.

### Input (before) — `src/main_ui_program.py`

```python
from .webserver_engine.webserve.src.launch_browser import launch_browser
...
    parser.add_argument('--db-file', type=str, required=True)
    args = parser.parse_args(*argcs, **kwargs)
...
    launch_browser(f'{config.get("http_address")}/')
    server.run()
```

### Output (after)

```python
from .browser_launcher import (
    BROWSER_MODE_DEFAULT, BROWSER_MODE_NOOP, BROWSER_MODE_PYWEBVIEW,
    launch_browser_for_mode,
)
...
    parser.add_argument('--browser', choices=[...], default=BROWSER_MODE_DEFAULT, ...)
    args = parser.parse_args(*argcs, **kwargs)
    if args.browser == BROWSER_MODE_PYWEBVIEW:
        raise NotImplementedError('--browser pywebview is not implemented yet')
...
    launch_browser_for_mode(args.browser, f'{config.get("http_address")}/')
    server.run()
```

### Repeat (to apply the same convention elsewhere)

1. Add a stdlib-only Python dev script at the repo root exposing idempotent
   `status`/`start`/`stop`/`restart`/`health` verbs with exit codes 0/1.
2. Record the spawned PID in a gitignored pid file; use an OS-branched
   port→PID lookup (`netstat` on Windows, `lsof` elsewhere) only as a fallback.
3. Health-check via an existing cheap endpoint (HTTP 200), not a new route.
4. Give the UI entry-point module a `--browser` flag whose values include a
   `no-op` for headless automation and a reserved `pywebview` that fails early.
5. Point the agent at the script with a skill (how-to, on demand) + a rule
   (one-line always-on pointer), and forbid `lsof`/`kill`/`sudo` in that context.
6. Add unit tests for the pure parts (mode dispatch, pid-file round-trip, health
   probe, arg parsing) without importing the heavy entry-point module.

---

## Entry-point imports: replace the three-branch `__name__` split with a two-branch `__package__` split

- **Requested:** 2026-11-04 18:09 MSK
- **Implemented:** 2026-11-04 18:20 MSK (reworked)
- **Where:** entry-point modules (`src/launcher.py` + the `--program` targets);
  the build script and run scripts are covered in the Repeat checklist.

### What & why

The launcher and the starter modules it dispatches to are the only files that
are *invoked* (as `__main__` via `-m`, or imported by the bundle); every other
module is only ever imported. The old code selected imports with a
**three-branch `__name__` split**:

- `if __name__ == '__main__'` — "run as a program",
- `elif '.' in __name__` — "imported as a package",
- `else` — "inlined with no parent package".

That three-branch split is confusing for two reasons: it is **not** the same as
the three invocation modes, and its `__main__` branch meant different things in
different projects (see the three "before" variants below). In practice the
`__main__` branch and the `else` branch always used the **same** flat imports, so
they collapse into one; the only real distinction is *inside a package* vs *no
parent package*, which `__package__` encodes directly.

Plain-script invocation (`python src/X.py`, without `-m`) is **dropped**: making
it work required a `sys.path` bootstrap and non-relative `src.*` imports, which
are not worth it. Supported invocation modes are the bundle and `-m`.

### Input (before) — three variants that grew out of the confusion

Variant A — classical three-branch, flat `__main__` (MDM-Diff-py `src/diff.py`,
commit `7baf51c`):

```python
if __name__ == '__main__':
    from diff_engine import diff_functions       # flat (script dir on sys.path)
elif '.' in __name__:
    from .diff_engine import diff_functions      # relative (package)
else:
    from diff_engine import diff_functions       # flat (no parent package)
```

Variant B — three-branch with `src.` in the `__main__` branch (apqa's original
`src/launcher.py`, to make `python -m src.launcher` work):

```python
if __name__ == '__main__':
    from src.GENERATED.VERSION import _VERSION   # absolute src.* (repo root on path)
elif '.' in __name__:
    from .GENERATED.VERSION import _VERSION      # relative (package)
else:
    from GENERATED.VERSION import _VERSION       # flat (no parent package)
```

Variant C — `_import_module` wrapper (MDM-Diff-py `src/launcher.py`):

```python
def _import_module(flat_name):
    if __name__ == '__main__':
        return importlib.import_module(flat_name)
    elif '.' in __name__:
        return importlib.import_module('.' + flat_name, package=__package__)
    else:
        return importlib.import_module(flat_name)
```

### Output (after) — two branches keyed on `__package__`

```python
if __package__:
    from .GENERATED.VERSION import _VERSION   # relative (package / -m / bundle)
else:
    from GENERATED.VERSION import _VERSION    # flat (no parent package)
```

Each entry-point module repeats this pattern for all its imports (one import is
shown here for brevity). No `sys.path` manipulation, no `src.*` absolute imports.

The bundle entry point is generated by pinliner (not hand-patched):

```bash
python pinliner/pinliner.py src -o dist/apqa_bundle.py --main src.launcher --main-attr main
```

### Repeat

1. **Entry-point modules** (the launcher and every module it dispatches to via
   `--program`) select imports on `__package__`:
   - `__package__` truthy → relative imports (`from .X import …`).
   - `__package__` falsy → flat imports (`from X import …`).
2. Give each starter module an `if __name__ == '__main__':` block that calls its
   entry function, so `python -m pkg.module` works.
3. **All other modules** use plain relative imports only.
4. **Bundle entry point** comes from pinliner `--main <module> --main-attr <attr>`
   (default attr `main`); the build script must **not** append `launcher.main()`.
5. **Drop plain-script support**: do not add `sys.path` hacks or `pkg.*` absolute
   imports to make `python pkg/module.py` work — use `-m` instead.


---

## maintenance-log: add a cross-project log for structural changes

- **Requested:** 2026-11-04 18:12 MSK
- **Implemented:** 2026-11-04 18:12 MSK
- **Where:** `docs/maintenance-log.md` (this file).

### What & why

The same structural conventions (import style, error reporting, output
coloring, argparse conventions, bundling/call conventions) are re-applied in
every project that shares the "launcher `--program` router + pinliner one-file
bundle" shape. Those need one dedicated place, separate from repo-specific
notes (`docs/project-context.md`) and the commit history, so they can be found
and repeated later. This file is that place.

### Input (before)

No dedicated file existed; structural notes were mixed into
`docs/project-context.md` and commit messages.

### Output (after)

`docs/maintenance-log.md` with a scoping header, a "How to read an entry"
format guide, and one section per structural change (**newest first**) — each
section headed like
a commit subject (intent + where) and answering When / What & why / Input /
Output / Repeat:

```markdown
# Maintenance log
> Cross-project maintenance notes. ...

## How to read an entry
- **When** — date/time requested and implemented.
- **What & why** — the request and the reasoning.
- **Input** — a sample of the code/file before the change.
- **Output** — a sample of the code/file after the change.
- **Repeat** — steps to apply the same convention in another project.

---

## <change title, like a commit subject>
- **Requested:** ...
- **Implemented:** ...
- **Where:** ...
### What & why
...
### Input (before)
...
### Output (after)
...
### Repeat
...
```

### Repeat

1. Create `docs/maintenance-log.md` in the repo's docs folder.
2. Add the scoping header + "How to read an entry" guide.
3. Add one section per structural change, **newest first**, in this exact shape.


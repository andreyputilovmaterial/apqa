# Architecture & imports (pinliner constraints)

The program is bundled with `pinliner` (submodule `src_dev_build/lib/pinliner`) into a single self-contained `apqa_bundle.py`. Everything here exists so that bundle keeps working.

## Imports

- Use **only relative imports** in `.py` files. The **only** exception is the set of *entry-point* modules: `src/launcher.py` and the starter scripts it dispatches to (`src/main_ui_program.py`, `src/main_init_program.py`, `src/main_print_help.py`). Each selects its imports on `__package__` — relative inside the `src` package, or flat (no parent package) otherwise. Plain-script invocation (`python src/X.py`, without `-m`) is **not** supported. See `docs/development.md` "Entry-point modules".
- Do **not** import from the top/outer level. If top-level code is genuinely needed: (1) `src/launcher.py` loads the starting module, (2) that module imports what it needs and stores it in a global config object, (3) the config object is passed down to where it is used. This is discouraged — avoid it.
- Every imported-module path **must** contain `__init__.py` at each level (pinliner requires this even though modern Python does not). When adding a package or submodule, ensure `__init__.py` exists.

## Runtime files

- The app must **not** depend on separate local files at runtime: no `.env`, no standalone JS/CSS assets, no `help.md`/`version.md`.
- Anything required at runtime must be **embedded in the bundle or importable as a Python module** (via `GENERATED/` folders produced by `build.sh`).
- This does **not** forbid reading *user-provided* files at runtime (e.g. source data given by full filesystem path in a QC rule).

## Bundling & submodules

- The distributable is produced by `build.sh` (output: `dist/apqa_bundle.py`). `build.sh` also generates the `GENERATED/` artifacts needed even for development runs.
- pinliner generates the bundle's `if __name__ == '__main__'` entry point via `--main src.launcher --main-attr main`; `build.sh` only appends the app-specific pytest entry point (`src_dev_build/bundle_pytest_postfix.py`) at the very end. Do **not** patch the bundle anywhere else — pinliner hard-codes module start/end positions.
- Reusable code is deliberately extracted into git submodules (an established habit in this repo). Prefer submodules for separable pieces.

# Optional dependencies

- The global `requirements.txt` lists only app-wide requirements.
- Per-cmdlet (and per-processor) extras are *optional*: keep a `requirements.txt`
  next to the component (encapsulation), e.g.
  `src/cmdlets/<name>/requirements.txt`.
- Optional deps may be platform-specific (`pywin32` → Windows only); a missing
  one is normal and must not break adding/editing/deleting rules.
- Each optional cmdlet guards its own import (`try/except`, storing the error) so
  the module always loads and the cmdlet is always registered; its runtime
  function raises a readable error (chained to the original) at its start. No
  global import-error machinery.
- `build.sh` auto-discovers the `requirements.txt` files (plain filesystem search
  on the source tree, before/outside the bundle) and inlines the installable
  specifiers as `pip install` statements into `dist/run_init.sh` /
  `dist/run_init.bat` (via `transform-run-script`). `run_init.*` installs each
  one best-effort (failure → WARNING, continue). No `dist/optional_dependencies/`
  folder is produced.

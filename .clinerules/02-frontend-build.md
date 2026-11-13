# Frontend & build

- The webserver is self-written (`src/webserver_engine/webserve`, submodule) — **no Flask/Django**.
- The webserver handles **all HTTP methods** (POST, etc.), even if it looks GET-only at first glance.
- Frontend apps may use **only `.js` and `.css`** — **no `.vue` and no `.ts`** (limitation of the self-written JS bundler `src/frontend/bundler_engine/lib/py_js_bundler`).
- The JS bundler is self-written and raw; it is being extended and may be replaced later.
- Prefer **relative imports** so components stay self-contained and liftable. The `@` alias (app root — `src/frontend/app_js/src`, from `jsconfig.json` → `compilerOptions.paths`) is resolved by both Vite and the self-written bundler; use `@/...` instead of deep `../../..` when a component must reach up to an outer level.
- The build must be possible **without Node installed**. Node/vite may be used only to speed up frontend development.
- `build.sh` is the single build entry point and must work after a fresh clone (it runs `git submodule update --init --recursive`).
- UI is Vue, but written as plain `.js` + `.css` (Vue served as a vendored JS asset), so it still satisfies the no-`.vue`/no-`.ts` rule.

## Dual run mode (npm dev vs bundle)

- The frontend runs two ways, and **both must keep working**: the Vite dev server
  (`npm install` + `npm run dev` inside `src/frontend/app_js`) and the
  backend-served `py_js_bundler` bundle (`build.sh` →
  `src/frontend/GENERATED/app.js`, served by the backend at `/assets/app.js`).
- The bundle needs **only Python** (plus its requirements) — no Node, Vite, or
  backend JS. The Vite dev server additionally needs **Node** and a **running
  backend**: Vite serves only the frontend and proxies every API call to
  `http://localhost:5280` (hard-coded in `src/frontend/app_js/vite.config.js`),
  so keep the backend on 5280 (or edit `vite.config.js`). If no backend change
  is needed, rely on Vite's hot reload alone.
- **While iterating on frontend-only changes, verify with the Vite dev server
  and do not re-run `py_js_bundler`/`build.sh` on every change.** The dev server
  exists to make frontend development fast; bundle-side regressions will be
  caught on your next full reload, so they are not silently missed. Re-run
  `build.sh` only when you need to test the real/final app (or to ship).
- If you can't reach the running frontend in a browser, ask the user (via
  helium-devtools MCP or a direct Chrome call) — the dev frontend should be
  reachable, otherwise ask.
- The npm/Vite dev server runs on Node's `http` server, whose `llhttp` parser
  rejects non-standard HTTP method names with `400 Bad Request` *before* Vite's
  proxy middleware sees them — the backend itself accepts any method name. Not a
  blocker for the bundle (no Node), but it can complicate development/tests, so
  prefer standard methods for anything the dev server must proxy.

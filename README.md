# APQA

APQA is a tool for **defining, managing, and running quality-control (QC) rules** for a research project.

A QC rule is a small, named check written as a pipeline of commands, for example:

```
get-content Specs.xlsx | select-sheet "Title Details" | select-column "B" | count
```

…compared against an expected result (here, a number). A rule describes *where* the
source data lives, *how* to read and transform it, and *what* result is expected.
Rules therefore serve both as documentation and as automated acceptance checks.

APQA runs in two ways:

1. **Desktop app — edit QC rules.** A local web UI (Python backend + Vue frontend,
   served from `localhost`) where you add, edit, rename, and delete rules. Changes
   are saved to the project's rules database file.
2. **Run the QC tests.** The same program is invoked through `pytest`, which
   executes every enabled rule against the source data and reports which rules
   passed and which failed.

## Quick start

You need Python 3 and a command line.

```bash
./build.sh        # produce the self-contained program into dist/
```

The run scripts work from the repo root (development) or from `dist/` (distribution):

```bash
./run_ui.sh       # open the desktop app (rule editor) in your browser
./run_tests.sh    # build, then run all QC rules as tests

cd dist           # or, after building, from the distributed folder:
./run_ui.sh
./run_tests.sh
```

The program ships as a single self-contained Python bundle (`dist/apqa_bundle.py`) —
no installation beyond Python.

The project to work on is selected by pointing the program at its **rules database
file** — a SQLite database by default (`.sqlite3`/`.sqlite`); YAML is also
supported (`.yaml`/`.yml`). The format is chosen by the file extension:

- Desktop app: `--db-file <path>` (see `run_ui.sh`).
- Run tests: the `APQA_DB_FILE` environment variable (see `run_tests.sh`).

The example run scripts contain a `DBFILE` variable pointing at a sample project file.
Edit it (or pass your own path) to select your project.

## Documentation

- **User guide** — the in-app **Help** page (content in [`help.md`](help.md)).
- **Developer / architecture guide** — [`docs/development.md`](docs/development.md).
- **Project state log** — [`docs/project-context.md`](docs/project-context.md).

## Under the hood (in one paragraph)

APQA is a Python program bundled into a single file with `pinliner`; it serves its UI
with a self-written web server (no Flask/Django) and bundles its JavaScript with a
self-written Python bundler, so building does **not** require Node. For these
implementation details, see the [developer guide](docs/development.md).

## License

[Apache License 2.0](LICENSE).

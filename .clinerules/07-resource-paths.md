# Resource paths

- A **resource path** is the address of a resource the app reads/writes (most
  often the QC-rules database file). It is either a **filesystem path**
  (yaml / json / sqlite) or a broader **resource address** that is not a
  physical file (e.g. an `oledb://` connection string). Only the filesystem
  kind can be resolved.
- **Store each path in the form that is stable for that resource:**
  - Prefer a **relative path** when the path is clearly scoped inside some root
    (a project, namespace, worktree, working directory, …) that carries it.
  - Prefer the **full resolved path** (`Path(path).resolve()` — absolute,
    symlinks resolved) when the path is just an independent location with no
    such root (like the QC-rules database file).
- **The QC-rules database file is an independent resource**, so its path is
  normalized to a full resolved path **once, at load time, inside the
  physical-file DB processor** (`DBFileYaml.__init__` / `DBFileSqlite.__init__`
  — the only place that knows the resource is a physical file). After that,
  `config['db_file']`, the page header, and the `path` returned by
  `GET /qc/project` all **carry the same resolved string through without
  transforming it**.
- **This applies only to filesystem paths.** Non-file resource addresses are
  stored and served exactly as given — never run them through filesystem path
  resolution. Decide by the resource type the DB processor detected
  (`src/db_processors/detect_type.py`), not by how the string looks.
- **Do not case-fold** (no `.lower()` / `.upper()` for case-insensitive
  filesystems): resolve to how the path is stored on the filesystem, nothing
  more.
- **The frontend must not normalize or compare-normalize paths.** A resource
  path is an opaque string to the browser (it may be a database id, a network
  address, …), so any normalization there would be guessing. The monitor
  compares the exact strings the backend serves (header vs `GET /qc/project`);
  since both come from the same already-resolved backend value, plain equality
  is sufficient.

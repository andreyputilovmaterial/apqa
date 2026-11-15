// Pure helpers for the cached QC-rule run results shown on a rule card. The
// path/note formatting mirrors the backend's `src/cmdlets/diagnostic.py`
// (`format_path`/`format_note`) so the UI renders the same short, human-readable
// data-path addresses the "run QC tests" output uses.

const IDENTIFIER = /^[A-Za-z_][A-Za-z0-9_]*$/;

// Render a data path (`['fields', 'A', 'label']`) as `fields.A.label`; array
// indices as `[i]`; non-identifier keys quoted, e.g. `['None of the above']`.
export function formatPath(path) {
  let result = '';
  for (const part of path || []) {
    if (typeof part === 'number') {
      result += `[${part}]`;
      continue;
    }
    const text = `${part == null ? '' : part}`;
    if (IDENTIFIER.test(text)) {
      if (result) result += '.';
      result += text;
    } else if (text.includes("'")) {
      result += `["${text.replace(/"/g, '\\"')}"]`;
    } else {
      result += `['${text}']`;
    }
  }
  return result;
}

// Render one note as `<path>: <message>` (or just the message).
export function formatNote(note) {
  const path = formatPath(note && note.path);
  const message = (note && note.message) || '';
  if (path) return `${path}: ${message}`;
  return message;
}

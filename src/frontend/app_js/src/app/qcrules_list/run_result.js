// Pure helpers for the cached QC-rule run results shown on a rule card. The
// path/note formatting mirrors the backend's `src/cmdlets/diagnostic.py`
// (`format_path`/`format_note`) so the UI renders the same short, human-readable
// data-path addresses the "run QC tests" output uses.

const IDENTIFIER = /^[A-Za-z_][A-Za-z0-9_]*$/;

// Render a data path (`['Fields', 'A', 'Label']`) as `Fields.A.Label`; array
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

// Map a cached run status to the gutter tick indicator shown next to a rule or
// folder. Returns `null` for `empty` (a folder with no rules inside, so nothing
// to show). `blank` (everything inside still un-run) and `indeterminate` (some
// passed, some blank) are folder-only states.
export function runTickFor(status) {
  switch (status) {
    case 'running':
      return { cls: 'is-running', icon: 'ri-loader-4-line', title: 'Running...' };
    case 'passed':
      return { cls: 'is-passed', icon: 'ri-check-line', title: 'Passed' };
    case 'failed':
    case 'error':
      return { cls: 'is-failed', icon: 'ri-close-fill', title: 'Failed' };
    case 'indeterminate':
      return { cls: 'is-indeterminate', text: '±', title: 'Indeterminate' };
    case 'blank':
      return { cls: 'is-empty', icon: '', text: '', title: '' };
    default:
      return null;
  }
}

// Render a folder's aggregated run counts as a short, pytest-like summary, e.g.
// `3 passed, 1 failed, 2 queued`. Zero counts are omitted. `counts` is the
// `runAggregate` object produced by `buildGroupNodes`.
export function groupRunSummary(counts) {
  if (!counts || !counts.total) return '';
  const parts = [];
  if (counts.passed) parts.push(`${counts.passed} passed`);
  if (counts.failed) parts.push(`${counts.failed} failed`);
  if (counts.errored) parts.push(`${counts.errored} error`);
  if (counts.running) parts.push(`${counts.running} running`);
  if (counts.blank) parts.push(`${counts.blank} queued`);
  return parts.join(', ');
}

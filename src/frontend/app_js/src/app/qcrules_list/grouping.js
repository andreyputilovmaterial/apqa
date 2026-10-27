// Pure helpers that turn a flat list of groups + rules into a flat, depth-first
// list of "nodes" (group folders interleaved with rule leaves). A single flat
// list keeps the renderer simple: the tree component only has to hide nodes
// whose ancestor folder is collapsed, no recursion in the template needed.

const orderOf = (value) => Number(value) || 0;

// ---- mark helpers -------------------------------------------------------------
// A rule carries stored markers (`skip`, `xfail`, …) and, on top of those, a
// derived `unfinished` mark when any of its three essential parts — left chain,
// comparison op, or right chain — is missing; such a rule is saved but cannot
// run. Mark *names* are shown as badges; their short CSS-class form drives the
// entry highlighting. Combined-mark color precedence is provisional (see
// docs/development.md "Markers").

// Turn a free-form marker name into a safe, short CSS class token.
export function markerClass(marker) {
  const text = String(marker == null ? '' : marker).trim();
  if (!text) return '';
  const slug = text
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9_-]+/g, '-')
    .replace(/^-+|-+$/g, '');
  if (!slug) return '';
  if (/^[0-9]/.test(slug)) return `mark-${slug}`;
  return slug;
}

// A rule is "unfinished" when the left side, comparison op, or right side is
// missing (saved mid-edit, therefore not runnable).
export function isUnfinished(record) {
  const left = Array.isArray(record.left) ? record.left : [];
  const right = Array.isArray(record.right) ? record.right : [];
  return left.length === 0 || !record.op || right.length === 0;
}

// Display mark names for a rule: its stored markers plus the derived
// `unfinished` mark. Deduplicated, stored order first, `unfinished` last.
export function markNamesForRecord(record) {
  const marks = [];
  const markers = Array.isArray(record.markers) ? record.markers : [];
  for (const marker of markers) {
    const name = String(marker == null ? '' : marker).trim();
    if (name && !marks.includes(name)) marks.push(name);
  }
  if (isUnfinished(record) && !marks.includes('unfinished')) {
    marks.push('unfinished');
  }
  return marks;
}

// Short CSS classes for a rule's marks (used for entry highlighting).
export function markClassesForRecord(record) {
  const classes = [];
  for (const mark of markNamesForRecord(record)) {
    const cls = markerClass(mark);
    if (cls && !classes.includes(cls)) classes.push(cls);
  }
  return classes;
}

export function buildGroupNodes(groups, records) {
  const byId = new Map();
  groups.forEach((group) => {
    byId.set(group.id, {
      id: group.id,
      name: group.name,
      parent: group.parent || '',
      order: orderOf(group.order),
      aliases: group.aliases || [],
      children: [],
      rules: [],
    });
  });

  // A group whose parent is missing/unknown becomes a root (defensive; the
  // backend refuses to create such references).
  const roots = [];
  byId.forEach((node) => {
    if (node.parent && byId.has(node.parent)) {
      byId.get(node.parent).children.push(node);
    } else {
      roots.push(node);
    }
  });

  const ungrouped = [];
  for (const record of records) {
    const group = record.group;
    if (group && byId.has(group)) byId.get(group).rules.push(record);
    else ungrouped.push(record);
  }

  const nodes = [];

  // Aggregated mark classes for a folder: the union of every rule's mark classes
  // anywhere inside it (recursively), so a single skipped/unfinished rule makes
  // its whole folder "marked" — like VSCode's changed files bubble up to their
  // folder. Memoized per node; `seen` guards against parent cycles.
  const groupMarkClassCache = new Map();
  function groupMarkClasses(node, seen = new Set()) {
    if (groupMarkClassCache.has(node.id)) return groupMarkClassCache.get(node.id);
    if (seen.has(node.id)) return [];
    seen.add(node.id);

    const classes = new Set();
    for (const rule of node.rules) {
      for (const cls of markClassesForRecord(rule)) classes.add(cls);
    }
    for (const child of node.children) {
      for (const cls of groupMarkClasses(child, seen)) classes.add(cls);
    }
    const result = Array.from(classes);
    groupMarkClassCache.set(node.id, result);
    return result;
  }

  // Same aggregation, but for display mark *names* (badges) rather than their
  // CSS-class form.
  const groupMarkCache = new Map();
  function groupMarks(node, seen = new Set()) {
    if (groupMarkCache.has(node.id)) return groupMarkCache.get(node.id);
    if (seen.has(node.id)) return [];
    seen.add(node.id);

    const marks = new Set();
    for (const rule of node.rules) {
      for (const mark of markNamesForRecord(rule)) marks.add(mark);
    }
    for (const child of node.children) {
      for (const mark of groupMarks(child, seen)) marks.add(mark);
    }
    const result = Array.from(marks);
    groupMarkCache.set(node.id, result);
    return result;
  }

  function pushRule(rule, depth, parents) {
    nodes.push({
      kind: 'rule',
      key: `r:${rule.id}`,
      id: rule.id,
      record: rule,
      depth,
      parents,
      marks: markNamesForRecord(rule),
      markClasses: markClassesForRecord(rule),
    });
  }

  function walk(node, depth, parents) {
    // Cycle guard; the backend prevents parent cycles, but stay safe.
    if (parents.includes(node.id)) return;
    nodes.push({
      kind: 'group',
      key: `g:${node.id}`,
      id: node.id,
      name: node.name,
      aliases: node.aliases || [],
      depth,
      parents: parents.slice(),
      marks: groupMarks(node),
      markClasses: groupMarkClasses(node),
    });
    const childParents = parents.concat(node.id);

    // Sibling sub-folders and rules are one ordered sequence (interleaved by
    // `order`, ties keep insertion order — sub-folders before rules).
    const entries = [];
    for (const child of node.children) entries.push({ order: child.order, group: child });
    for (const rule of node.rules) entries.push({ order: orderOf(rule.order), rule });
    entries.sort((a, b) => a.order - b.order);
    for (const entry of entries) {
      if (entry.group) walk(entry.group, depth + 1, childParents);
      else pushRule(entry.rule, depth + 1, childParents);
    }
  }

  // Top level: ungrouped rules and root groups are siblings, ordered the same way.
  const top = [];
  for (const rule of ungrouped) top.push({ order: orderOf(rule.order), rule });
  for (const root of roots) top.push({ order: root.order, group: root });
  top.sort((a, b) => a.order - b.order);
  for (const entry of top) {
    if (entry.group) walk(entry.group, 0, []);
    else pushRule(entry.rule, 0, []);
  }

  return nodes;
}

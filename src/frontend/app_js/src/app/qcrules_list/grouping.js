// Pure helpers that turn a flat list of groups + rules into a flat, depth-first
// list of "nodes" (group folders interleaved with rule leaves). A single flat
// list keeps the renderer simple: the tree component only has to hide nodes
// whose ancestor folder is collapsed, no recursion in the template needed.

const orderOf = (value) => Number(value) || 0;

// ---- mark helpers -------------------------------------------------------------
// A rule carries stored markers (`skip`, `xfail`, …) and, on top of those, a
// derived `unfinished` mark when any essential piece of the rule is `sysmissing`
// (`null`/`undefined`): an empty left chain, an unset comparison op, an empty
// right chain, or a required argument (recursively into nested chains) that is
// missing. A piece that is present but unrecognized (e.g. a cmdlet name unknown
// to this environment) is NOT missing — it fails at run time instead. Mark
// *names* are shown as badges; their short CSS-class form drives the entry
// highlighting. Combined-mark color precedence is provisional (see
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

// A rule is "unfinished" when any essential piece is `sysmissing` — a
// "disconnect" in the rule's logic. A piece is missing when its value is
// `null`/`undefined` (or, for a chain-typed argument, an empty chain): an empty
// left chain, an unset comparison op, an empty right chain, or a required
// argument whose value is `sysmissing` (recursively into nested
// `cmdlet-chain`/`cmdlet-chains` args). A piece that is present but not
// *recognized* (e.g. a cmdlet name unknown to this environment) is NOT missing
// — it is a value, and it fails at run time instead.
export function isMissing(value, type) {
  if (value === null || value === undefined) return true;
  if (type === 'cmdlet-chain' || type === 'cmdlet-chains') {
    return !Array.isArray(value) || value.length === 0;
  }
  return false;
}

// Problems in one chain of cmdlets. Unknown cmdlet names are skipped (they are
// not "missing" — they fail at run time).
function chainProblems(chain, cmdlets) {
  const problems = [];
  for (const step of chain || []) {
    if (!step || typeof step !== 'object') continue;
    const meta = (cmdlets || []).find((c) => c.name === step.cmdlet);
    if (!meta) continue;
    for (const arg of meta.args || []) {
      if (!arg.required) continue;
      const value =
        step.args && typeof step.args === 'object' ? step.args[arg.name] : undefined;
      if (isMissing(value, arg.type)) {
        problems.push(`${step.cmdlet}: missing required arg '${arg.name}'`);
        continue;
      }
      if (arg.type === 'cmdlet-chain') {
        problems.push(...chainProblems(value, cmdlets));
      } else if (arg.type === 'cmdlet-chains') {
        for (const nested of value) problems.push(...chainProblems(nested, cmdlets));
      }
    }
  }
  return problems;
}

// All missing pieces of a rule: an empty left chain, an unset comparison op, an
// empty right chain, or any required argument (recursively, including required
// op_args) whose value is `sysmissing`.
export function ruleProblems(record, cmdlets = [], ops = []) {
  const problems = [];
  const left = Array.isArray(record.left) ? record.left : [];
  const right = Array.isArray(record.right) ? record.right : [];

  if (left.length === 0) problems.push('left side is missing');
  else problems.push(...chainProblems(left, cmdlets));

  if (!record.op) problems.push('comparison op is missing');
  else {
    const opMeta = (ops || []).find((o) => o.name === record.op);
    for (const arg of (opMeta && opMeta.op_args) || []) {
      if (!arg.required) continue;
      const value =
        record.op_args && typeof record.op_args === 'object'
          ? record.op_args[arg.name]
          : undefined;
      if (isMissing(value, arg.type)) {
        problems.push(`op '${record.op}': missing required arg '${arg.name}'`);
      }
    }
  }

  if (right.length === 0) problems.push('right side is missing');
  else problems.push(...chainProblems(right, cmdlets));

  return problems;
}

export function isUnfinished(record, cmdlets = [], ops = []) {
  return ruleProblems(record, cmdlets, ops).length > 0;
}

// Display mark names for a rule: its stored markers plus the derived
// `unfinished` mark. Deduplicated, stored order first, `unfinished` last.
export function markNamesForRecord(record, cmdlets, ops) {
  const marks = [];
  const markers = Array.isArray(record.markers) ? record.markers : [];
  for (const marker of markers) {
    const name = String(marker == null ? '' : marker).trim();
    if (name && !marks.includes(name)) marks.push(name);
  }
  if (isUnfinished(record, cmdlets, ops) && !marks.includes('unfinished')) {
    marks.push('unfinished');
  }
  return marks;
}

// Short CSS classes for a rule's marks (used for entry highlighting).
export function markClassesForRecord(record, cmdlets, ops) {
  const classes = [];
  for (const mark of markNamesForRecord(record, cmdlets, ops)) {
    const cls = markerClass(mark);
    if (cls && !classes.includes(cls)) classes.push(cls);
  }
  return classes;
}

export function buildGroupNodes(groups, records, cmdlets = [], ops = []) {
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
      for (const cls of markClassesForRecord(rule, cmdlets, ops)) classes.add(cls);
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
      for (const mark of markNamesForRecord(rule, cmdlets, ops)) marks.add(mark);
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
      marks: markNamesForRecord(rule, cmdlets, ops),
      markClasses: markClassesForRecord(rule, cmdlets, ops),
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

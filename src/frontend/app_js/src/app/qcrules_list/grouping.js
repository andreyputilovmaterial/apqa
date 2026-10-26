// Pure helpers that turn a flat list of groups + rules into a flat, depth-first
// list of "nodes" (group folders interleaved with rule leaves). A single flat
// list keeps the renderer simple: the tree component only has to hide nodes
// whose ancestor folder is collapsed, no recursion in the template needed.

const orderOf = (value) => Number(value) || 0;

export function buildGroupNodes(groups, records) {
  const byName = new Map();
  groups.forEach((group) => {
    byName.set(group.name, {
      id: group.name,
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
  byName.forEach((node) => {
    if (node.parent && byName.has(node.parent)) {
      byName.get(node.parent).children.push(node);
    } else {
      roots.push(node);
    }
  });

  const ungrouped = [];
  for (const record of records) {
    const group = record.group;
    if (group && byName.has(group)) byName.get(group).rules.push(record);
    else ungrouped.push(record);
  }

  const nodes = [];

  function pushRule(rule, depth, parents) {
    nodes.push({
      kind: 'rule',
      key: `r:${rule.id}`,
      id: rule.id,
      record: rule,
      depth,
      parents,
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

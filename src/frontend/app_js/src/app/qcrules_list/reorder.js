// Pure helpers for drag-and-drop reordering of the QC-rules tree. They turn a
// `(dragged node, target node, drop position)` triple into a move descriptor the
// backend understands — `{ kind, id, parent, before }` — plus the validation a
// drop needs (no parent cycles, no no-op moves).
//
// `nodes` is the flat, depth-first, already-ordered list returned by
// `buildGroupNodes` (see grouping.js). Every node carries `key` (`r:<id>` /
// `g:<id>`), `kind`, `id`, and `parents` (ancestor group ids, outermost first).

// The immediate parent group id of a node ('' = top level).
export function parentIdOf(node) {
  return node && node.parents && node.parents.length
    ? node.parents[node.parents.length - 1]
    : '';
}

// All nodes whose immediate parent is `parentId`, in their existing display order.
export function siblingsOf(nodes, parentId) {
  return nodes.filter((node) => parentIdOf(node) === parentId);
}

// The group node with the given id, or null.
export function groupNodeById(nodes, id) {
  return nodes.find((node) => node.kind === 'group' && node.id === id) || null;
}

// Would moving a group with id `draggedGroupId` under `parentId` close a cycle
// (i.e. `parentId` is the group itself or one of its descendants)?
export function wouldCreateCycle(nodes, draggedGroupId, parentId) {
  if (!parentId) return false;
  if (parentId === draggedGroupId) return true;
  const parentNode = groupNodeById(nodes, parentId);
  if (!parentNode) return false;
  return (parentNode.parents || []).includes(draggedGroupId);
}

// Whether the move lands the dragged node back where it already is, relative to
// its siblings — in which case nothing should be sent to the backend.
export function isNoOp(dragged, parentId, before, nodes) {
  if (parentId !== parentIdOf(dragged)) return false;
  const current = siblingsOf(nodes, parentId).map((node) => node.key);
  const without = current.filter((key) => key !== dragged.key);
  let index;
  if (before === null) {
    index = without.length;
  } else {
    index = without.indexOf(before);
    if (index === -1) index = without.length;
  }
  const next = without.slice();
  next.splice(index, 0, dragged.key);
  return next.join('\u0000') === current.join('\u0000');
}

// Turn a drop into a move descriptor, or return null when the drop is not valid
// (invalid position, a cycle for a dragged folder, or a no-op). `position` is
// 'before' | 'after' | 'inside'. `before` is the prefixed sibling key to insert
// before (null = append at the end of `parent`).
export function moveDescriptor(dragged, target, position, nodes) {
  if (!dragged || !target) return null;

  const targetParent = parentIdOf(target);
  let parentId;
  let before;

  if (position === 'inside') {
    if (target.kind !== 'group') return null;
    parentId = target.id;
    before = null;
  } else if (position === 'before' || position === 'after') {
    parentId = targetParent;
    // Insertion is computed against the sibling list with the dragged node
    // removed, so a drop "after" a node that currently precedes the dragged node
    // still resolves to the correct anchor.
    const siblings = siblingsOf(nodes, targetParent).filter(
      (node) => node.key !== dragged.key,
    );
    const targetIndex = siblings.findIndex((node) => node.key === target.key);
    if (position === 'before') {
      before = target.key;
    } else {
      const next =
        targetIndex >= 0 && targetIndex < siblings.length - 1
          ? siblings[targetIndex + 1]
          : null;
      before = next ? next.key : null;
    }
  } else {
    return null;
  }

  if (dragged.kind === 'group' && wouldCreateCycle(nodes, dragged.id, parentId)) {
    return null;
  }

  if (isNoOp(dragged, parentId, before, nodes)) {
    return null;
  }

  return { kind: dragged.kind, id: dragged.id, parent: parentId, before };
}

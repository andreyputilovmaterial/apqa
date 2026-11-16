import { describe, it, expect } from 'vitest';

import {
  groupNodeById,
  isNoOp,
  moveDescriptor,
  parentIdOf,
  siblingsOf,
  wouldCreateCycle,
} from './reorder.js';

function ruleNode(id, parents = []) {
  return { key: `r:${id}`, kind: 'rule', id, parents };
}

function groupNode(id, parents = []) {
  return { key: `g:${id}`, kind: 'group', id, parents };
}

describe('parentIdOf', () => {
  it('returns the innermost parent group id, or empty at top level', () => {
    expect(parentIdOf(ruleNode('a'))).toBe('');
    expect(parentIdOf(ruleNode('a', ['data']))).toBe('data');
    expect(parentIdOf(groupNode('a', ['data', 'meta']))).toBe('meta');
  });
});

describe('siblingsOf', () => {
  it('returns only nodes whose immediate parent matches', () => {
    const nodes = [
      groupNode('data'),
      groupNode('meta', ['data']),
      ruleNode('r1', ['data']),
      ruleNode('r2', ['data']),
      ruleNode('r3'),
    ];
    expect(siblingsOf(nodes, 'data').map((n) => n.key)).toEqual(['g:meta', 'r:r1', 'r:r2']);
    expect(siblingsOf(nodes, '').map((n) => n.key)).toEqual(['g:data', 'r:r3']);
  });
});

describe('groupNodeById', () => {
  it('finds a group node by id, ignoring rules', () => {
    const nodes = [ruleNode('x'), groupNode('data')];
    expect(groupNodeById(nodes, 'data').key).toBe('g:data');
    expect(groupNodeById(nodes, 'x')).toBeNull();
  });
});

describe('wouldCreateCycle', () => {
  it('detects a self-parent and a descendant parent', () => {
    const nodes = [groupNode('a'), groupNode('b', ['a']), groupNode('c', ['a', 'b'])];
    expect(wouldCreateCycle(nodes, 'a', 'a')).toBe(true);
    expect(wouldCreateCycle(nodes, 'a', 'b')).toBe(true);
    expect(wouldCreateCycle(nodes, 'a', 'c')).toBe(true);
    expect(wouldCreateCycle(nodes, 'b', 'a')).toBe(false);
    expect(wouldCreateCycle(nodes, 'b', '')).toBe(false);
  });
});

describe('isNoOp', () => {
  it('is true when the item ends up in the same sibling position', () => {
    const nodes = [ruleNode('r1'), ruleNode('r2'), ruleNode('r3')];
    expect(isNoOp(ruleNode('r1'), '', 'r:r2', nodes)).toBe(true); // r1 already before r2
    expect(isNoOp(ruleNode('r1'), '', null, nodes)).toBe(false); // r1 would append at end
    expect(isNoOp(ruleNode('r2'), '', 'r:r3', nodes)).toBe(true); // r2 already before r3
  });
});

describe('moveDescriptor', () => {
  it('moves a rule before another top-level rule', () => {
    const nodes = [ruleNode('r1'), ruleNode('r2'), ruleNode('r3')];
    expect(moveDescriptor(ruleNode('r3'), ruleNode('r1'), 'before', nodes)).toEqual({
      kind: 'rule',
      id: 'r3',
      parent: '',
      before: 'r:r1',
    });
  });

  it('moves a rule after another, anchoring on the following sibling', () => {
    const nodes = [ruleNode('r1'), ruleNode('r2'), ruleNode('r3')];
    expect(moveDescriptor(ruleNode('r3'), ruleNode('r1'), 'after', nodes)).toEqual({
      kind: 'rule',
      id: 'r3',
      parent: '',
      before: 'r:r2',
    });
  });

  it('appends when dropping after the last sibling', () => {
    const nodes = [ruleNode('r1'), ruleNode('r2')];
    expect(moveDescriptor(ruleNode('r1'), ruleNode('r2'), 'after', nodes)).toEqual({
      kind: 'rule',
      id: 'r1',
      parent: '',
      before: null,
    });
  });

  it('moves a rule inside a folder', () => {
    const nodes = [groupNode('data'), ruleNode('r1')];
    expect(moveDescriptor(ruleNode('r1'), groupNode('data'), 'inside', nodes)).toEqual({
      kind: 'rule',
      id: 'r1',
      parent: 'data',
      before: null,
    });
  });

  it('rejects a no-op drop back to the same position', () => {
    const nodes = [ruleNode('r1'), ruleNode('r2'), ruleNode('r3')];
    // r1 already sits right before r2: dropping it "before r2" is a no-op.
    expect(moveDescriptor(ruleNode('r1'), ruleNode('r2'), 'before', nodes)).toBeNull();
    // r2 already sits right after r1: dropping it "after r1" is a no-op.
    expect(moveDescriptor(ruleNode('r2'), ruleNode('r1'), 'after', nodes)).toBeNull();
  });

  it('rejects dropping a folder inside its own descendant', () => {
    const nodes = [groupNode('a'), groupNode('b', ['a'])];
    expect(moveDescriptor(groupNode('a'), groupNode('b'), 'inside', nodes)).toBeNull();
  });
});

import { describe, it, expect } from 'vitest';

import { buildGroupNodes } from './grouping.js';

function rule(name, group = '', order = 0) {
  return { id: name, name, group, order };
}

function group(name, parent = '', order = 0) {
  return { name, parent, order };
}

describe('buildGroupNodes', () => {
  it('flattens nested groups depth-first with correct depths', () => {
    const nodes = buildGroupNodes(
      [group('Data'), group('Metadata', 'Data'), group('Routing')],
      [rule('r1', 'Metadata')],
    );

    const names = nodes.map((n) => (n.kind === 'rule' ? n.record.name : n.name));
    expect(names).toEqual(['Data', 'Metadata', 'r1', 'Routing']);

    const metadata = nodes.find((n) => n.name === 'Metadata');
    expect(metadata.depth).toBe(1);
    expect(metadata.parents).toEqual(['Data']);
  });

  it('assigns rules to their group with the right depth and parents', () => {
    const nodes = buildGroupNodes(
      [group('Data'), group('Metadata', 'Data')],
      [rule('r1', 'Data'), rule('r2', 'Metadata')],
    );

    const r2 = nodes.find((n) => n.kind === 'rule' && n.record.name === 'r2');
    expect(r2.depth).toBe(2);
    expect(r2.parents).toEqual(['Data', 'Metadata']);
  });

  it('puts ungrouped rules at the top level (no synthetic folder)', () => {
    const nodes = buildGroupNodes([group('Data')], [rule('r1'), rule('r2')]);

    const ruleNodes = nodes.filter((n) => n.kind === 'rule');
    expect(ruleNodes.map((n) => n.record.name)).toEqual(['r1', 'r2']);
    expect(ruleNodes[0].depth).toBe(0);
    expect(ruleNodes[0].parents).toEqual([]);
    expect(nodes.some((n) => n.kind === 'group' && n.name === 'Ungrouped')).toBe(false);
  });

  it('treats rules in an unknown group as ungrouped', () => {
    const nodes = buildGroupNodes([], [rule('r1', 'Ghost')]);
    expect(nodes.map((n) => n.record.name)).toEqual(['r1']);
    expect(nodes[0].depth).toBe(0);
    expect(nodes[0].parents).toEqual([]);
  });

  it('keeps empty groups', () => {
    const nodes = buildGroupNodes([group('Empty')], []);
    expect(nodes.map((n) => n.name)).toEqual(['Empty']);
  });

  it('treats a group with a missing parent as a root', () => {
    const nodes = buildGroupNodes([group('Child', 'Ghost')], []);
    expect(nodes.map((n) => n.name)).toEqual(['Child']);
    expect(nodes[0].parents).toEqual([]);
  });

  it('interleaves sub-folders and rules by their order', () => {
    const nodes = buildGroupNodes(
      [
        group('titles updated', '', 0),
        group('titles are matching excel', 'titles updated', 0),
        group('properties match', 'titles are matching excel', 1),
        group('descriptions match', 'titles are matching excel', 3),
      ],
      [
        rule('labels match', 'titles are matching excel', 0),
        rule('Zootopia 2 pipe in is updated', 'titles are matching excel', 2),
      ],
    );

    const names = nodes.map((n) => (n.kind === 'rule' ? n.record.name : n.name));
    expect(names).toEqual([
      'titles updated',
      'titles are matching excel',
      'labels match',
      'properties match',
      'Zootopia 2 pipe in is updated',
      'descriptions match',
    ]);
  });

  it('terminates on a parent cycle', () => {
    const nodes = buildGroupNodes([group('A', 'B'), group('B', 'A')], []);
    expect(nodes).toEqual([]);
  });
});

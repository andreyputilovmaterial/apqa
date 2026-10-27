import { describe, it, expect } from 'vitest';

import {
  buildGroupNodes,
  isUnfinished,
  markClassesForRecord,
  markNamesForRecord,
  markerClass,
} from './grouping.js';

function rule(name, group = '', order = 0, extra = {}) {
  return {
    id: name,
    name,
    group,
    order,
    markers: [],
    left: [],
    op: '',
    right: [],
    ...extra,
  };
}

function group(name, parent = '', order = 0, aliases = []) {
  return { id: name, name, parent, order, aliases };
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

  it('carries folder aliases onto group nodes', () => {
    const aliases = [
      { name: 'survey_mdd', chain: [{ cmdlet: 'get-content-mdd', args: { path: 'x' } }] },
    ];
    const nodes = buildGroupNodes([group('Data', '', 0, aliases)], []);
    const node = nodes.find((n) => n.kind === 'group');
    expect(node.aliases).toEqual(aliases);
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

describe('marks', () => {
  it('maps markers to short, safe CSS class names', () => {
    expect(markerClass('skip')).toBe('skip');
    expect(markerClass('xfail')).toBe('xfail');
    expect(markerClass('Win 32')).toBe('win-32');
    expect(markerClass('')).toBe('');
    expect(markerClass(undefined)).toBe('');
  });

  it('treats a rule as unfinished when any of left, op or right is missing', () => {
    const left = [{ cmdlet: 'count' }];
    const right = [{ cmdlet: 'count' }];
    expect(isUnfinished(rule('r', '', 0, { left, op: '', right: [] }))).toBe(true);
    expect(isUnfinished(rule('r', '', 0, { left, op: 'eq', right: [] }))).toBe(true);
    expect(isUnfinished(rule('r', '', 0, { left: [], op: 'eq', right }))).toBe(true);
    expect(isUnfinished(rule('r', '', 0, { left: [], op: '', right: [] }))).toBe(true);
    expect(isUnfinished(rule('r', '', 0, { left, op: 'eq', right }))).toBe(false);
  });

  it('returns marker classes plus a derived unfinished class', () => {
    const left = [{ cmdlet: 'count' }];
    expect(
      markClassesForRecord(rule('r', '', 0, { markers: ['skip', 'xfail'], left, op: '', right: [] })),
    ).toEqual(['skip', 'xfail', 'unfinished']);
    expect(
      markClassesForRecord(rule('r', '', 0, { markers: ['skip'], left, op: 'eq', right: [{ cmdlet: 'count' }] })),
    ).toEqual(['skip']);
  });

  it('returns display mark names including a derived unfinished mark', () => {
    const left = [{ cmdlet: 'count' }];
    expect(
      markNamesForRecord(rule('r', '', 0, { markers: ['skip', 'xfail'], left, op: '', right: [] })),
    ).toEqual(['skip', 'xfail', 'unfinished']);
    expect(
      markNamesForRecord(rule('r', '', 0, { left, op: 'eq', right: [{ cmdlet: 'count' }] })),
    ).toEqual([]);
  });

  it('aggregates rule mark classes up to ancestor folders', () => {
    const left = [{ cmdlet: 'count' }];
    const nodes = buildGroupNodes(
      [group('Data'), group('Metadata', 'Data')],
      [
        rule('r1', 'Data', 0, { markers: ['skip'], left, op: 'eq', right: [{ cmdlet: 'count' }] }),
        rule('r2', 'Metadata', 0, { left, op: '', right: [] }),
      ],
    );

    const data = nodes.find((n) => n.kind === 'group' && n.name === 'Data');
    const metadata = nodes.find((n) => n.kind === 'group' && n.name === 'Metadata');
    const r1 = nodes.find((n) => n.kind === 'rule' && n.record.name === 'r1');

    expect(r1.markClasses).toEqual(['skip']);
    expect(metadata.markClasses).toEqual(['unfinished']);
    expect(data.markClasses).toEqual(['skip', 'unfinished']);
    expect(r1.marks).toEqual(['skip']);
    expect(metadata.marks).toEqual(['unfinished']);
    expect(data.marks).toEqual(['skip', 'unfinished']);
  });
});


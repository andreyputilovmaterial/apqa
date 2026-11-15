import { describe, it, expect } from 'vitest';
import { opSpec } from './shared.js';

describe('opSpec', () => {
  it('returns the declared display spec for an op in a given form', () => {
    const ops = [{ name: 'eq', compact: [{ text: '=', role: 'symbol' }] }];
    expect(opSpec(ops, 'eq', 'compact')).toEqual([{ text: '=', role: 'symbol' }]);
  });

  it('returns null when the op is unknown', () => {
    expect(opSpec([{ name: 'eq', compact: [] }], 'contains', 'compact')).toBe(null);
  });

  it('returns null when the form is not declared for that op', () => {
    const ops = [{ name: 'eq', compact: [{ text: '=' }] }];
    expect(opSpec(ops, 'eq', 'full')).toBe(null);
    expect(opSpec([], 'eq', 'compact')).toBe(null);
  });
});

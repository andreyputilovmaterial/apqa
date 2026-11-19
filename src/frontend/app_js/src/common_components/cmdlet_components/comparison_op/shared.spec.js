import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import { opSpec } from './shared.js';
import ComparisonOpCompact from './compact.js';

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

describe('comparison op compact', () => {
  it('wraps the symbol with tab separators for copy-as-text', () => {
    const ops = [{ name: 'eq', compact: [{ text: '=', role: 'symbol' }] }];
    const wrapper = mount(ComparisonOpCompact, { props: { op: 'eq', ops } });

    // `textContent` (not `wrapper.text()`, which trims) keeps the leading and
    // trailing tab separators that only matter for copy-as-text.
    expect(wrapper.element.textContent).toBe('\t=\t');
  });

  it('falls back to the raw op name when no spec is declared', () => {
    const wrapper = mount(ComparisonOpCompact, { props: { op: 'eq', ops: [] } });

    expect(wrapper.element.textContent).toBe('\teq\t');
  });
});

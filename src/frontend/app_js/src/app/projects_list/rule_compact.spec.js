import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import RuleCompact from './rule_compact.js';

function makeRecord(overrides = {}) {
  return {
    name: 'Rule A',
    comment: '',
    left: [{ cmdlet: 'get-content', args: { path: 'a.sav' } }],
    op: 'eq',
    right: [{ cmdlet: 'count' }],
    _filterMeta: { cssClasses: '' },
    ...overrides,
  };
}

describe('RuleCompact', () => {
  it('renders the name and both sides of the rule', () => {
    const wrapper = mount(RuleCompact, { props: { record: makeRecord() } });
    const text = wrapper.text();

    expect(text).toContain('Rule A');
    expect(text).toContain('get-content path=a.sav');
    expect(text).toContain('=');
    expect(text).toContain('count');
  });

  it('renders the comment only when present', () => {
    const withComment = mount(RuleCompact, {
      props: { record: makeRecord({ comment: 'check the count' }) },
    });
    expect(withComment.text()).toContain('check the count');

    const withoutComment = mount(RuleCompact, {
      props: { record: makeRecord() },
    });
    expect(withoutComment.text()).not.toContain('check the count');
  });
});

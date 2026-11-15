import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import RuleCompact from './rule_compact.js';
import { UNFINISHED_MESSAGE } from './marks_badges.js';
import { cmdletComponents } from '@/common_components/cmdlet_components/index.js';

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

// `rule_compact` renders cmdlets through the globally-registered display
// components; register them for the mount (same set as app.js).
const GLOBAL = { components: cmdletComponents };

function mountCompact(props = {}) {
  return mount(RuleCompact, { global: GLOBAL, props });
}

describe('RuleCompact', () => {
  it('renders the name and both sides of the rule', () => {
    const wrapper = mountCompact({ record: makeRecord() });
    const text = wrapper.text();

    expect(text).toContain('Rule A');
    expect(text).toContain('get-content path=a.sav');
    expect(text).toContain('=');
    expect(text).toContain('count');
  });

  it('shows a down-double arrow on the name hinting it expands', () => {
    const wrapper = mountCompact({ record: makeRecord() });
    expect(wrapper.find('.apqa-rule-compact-name .ri-arrow-down-double-fill').exists()).toBe(true);
  });

  it('renders the comment only when present', () => {
    const withComment = mountCompact({ record: makeRecord({ comment: 'check the count' }) });
    expect(withComment.text()).toContain('check the count');

    const withoutComment = mountCompact({ record: makeRecord() });
    expect(withoutComment.text()).not.toContain('check the count');
  });

  it('emits toggle when the description line is clicked', async () => {
    const wrapper = mountCompact({ record: makeRecord() });
    await wrapper.find('.apqa-rule-compact-description').trigger('click');
    expect(wrapper.emitted('toggle')).toHaveLength(1);
  });

  it('does not render a badges line for an unmarked rule', () => {
    const wrapper = mountCompact({ record: makeRecord() });
    expect(wrapper.find('.apqa-marks-badges').exists()).toBe(false);
  });

  it('renders mark badges as the last line', () => {
    const wrapper = mountCompact({ record: makeRecord({ markers: ['skip', 'xfail'] }) });

    const badges = wrapper.findAll('.apqa-mark-badge');
    expect(badges.map((badge) => badge.text())).toEqual(['skip', 'xfail']);
  });

  it('shows an unfinished helper note under the name', () => {
    const wrapper = mountCompact({ record: makeRecord({ op: '', right: [] }) });

    expect(wrapper.find('.apqa-rule-unfinished-note').text()).toBe(UNFINISHED_MESSAGE);
    expect(wrapper.find('.apqa-mark-badge-unfinished').exists()).toBe(true);
  });
});

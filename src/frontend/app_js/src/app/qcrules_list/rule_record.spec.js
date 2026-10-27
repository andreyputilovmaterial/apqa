import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import RuleRecord from './rule_record.js';

function makeRecord(overrides = {}) {
  return {
    name: 'Rule A',
    comment: 'check the count',
    left: [{ cmdlet: 'get-content', args: { path: 'a.sav' } }],
    op: 'eq',
    right: [{ cmdlet: 'count' }],
    markers: [],
    tags: [],
    created_at: '',
    _filterMeta: { cssClasses: [] },
    ...overrides,
  };
}

describe('RuleRecord', () => {
  it('starts collapsed (compact view, no actions)', () => {
    const wrapper = mount(RuleRecord, { props: { record: makeRecord() } });
    expect(wrapper.find('.apqa-rule-compact').exists()).toBe(true);
    expect(wrapper.find('.apqa-rule-body-action').exists()).toBe(false);
  });

  it('expands to the full view on header click and shows actions', async () => {
    const wrapper = mount(RuleRecord, { props: { record: makeRecord() } });
    await wrapper.find('.apqa-rule-compact-description').trigger('click');

    expect(wrapper.find('.apqa-qcrules-list-item').exists()).toBe(true);
    const actions = wrapper.findAll('.apqa-rule-body-action');
    expect(actions.map((a) => a.text())).toEqual(['Edit', 'Run', 'Delete']);
  });

  it('collapses back to compact view on a second header click', async () => {
    const wrapper = mount(RuleRecord, { props: { record: makeRecord() } });
    await wrapper.find('.apqa-rule-compact-description').trigger('click');
    expect(wrapper.find('.apqa-qcrules-list-item').exists()).toBe(true);

    await wrapper.find('.apqa-qcrules-list-item-head').trigger('click');
    expect(wrapper.find('.apqa-rule-compact').exists()).toBe(true);
    expect(wrapper.find('.apqa-rule-body-action').exists()).toBe(false);
  });

  it('forwards edit, run and delete actions with the record', async () => {
    const wrapper = mount(RuleRecord, { props: { record: makeRecord() } });
    await wrapper.find('.apqa-rule-compact-description').trigger('click');

    const buttons = wrapper.findAll('.apqa-rule-body-action');
    await buttons[0].trigger('click');
    await buttons[1].trigger('click');
    await buttons[2].trigger('click');

    expect(wrapper.emitted('edit')).toHaveLength(1);
    expect(wrapper.emitted('edit')[0][0]).toMatchObject({ name: 'Rule A' });
    expect(wrapper.emitted('run')).toHaveLength(1);
    expect(wrapper.emitted('run')[0][0]).toMatchObject({ name: 'Rule A' });
    expect(wrapper.emitted('delete')).toHaveLength(1);
    expect(wrapper.emitted('delete')[0][0]).toMatchObject({ name: 'Rule A' });
  });
});

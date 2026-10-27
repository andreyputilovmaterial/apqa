import { describe, it, expect, vi } from 'vitest';
import { mount } from '@vue/test-utils';

import RulesTree from './rules_tree.js';

function rule(name, group = '', extra = {}) {
  return {
    id: name,
    name,
    group,
    comment: '',
    left: [],
    op: '',
    right: [],
    markers: [],
    tags: [],
    created_at: '',
    _filterMeta: { cssClasses: [] },
    ...extra,
  };
}

function group(name, parent = '', aliases = []) {
  return { id: name, name, parent, aliases };
}

// `input_cmdlet` references the chain component by its global name for the
// `cmdlet-chains` arg type; a stub silences the resolution warning when the
// inline edit form renders.
const ChainStub = { template: '<div class="chain-stub" />' };

describe('RulesTree', () => {
  it('starts with folders folded and expands on click', async () => {
    const wrapper = mount(RulesTree, {
      props: {
        groups: [group('Data')],
        records: [rule('r1', 'Data')],
      },
    });

    expect(wrapper.text()).toContain('Data');
    expect(wrapper.text()).toContain('[+]');
    expect(wrapper.text()).not.toContain('r1');

    await wrapper.find('.apqa-rules-tree-group-header').trigger('click');

    expect(wrapper.text()).toContain('Data');
    expect(wrapper.text()).toContain('[-]');
    expect(wrapper.text()).toContain('r1');

    await wrapper.find('.apqa-rules-tree-group-header').trigger('click');

    expect(wrapper.text()).toContain('[+]');
    expect(wrapper.text()).not.toContain('r1');
  });

  it('renders ungrouped rules directly, without a folder heading', () => {
    const wrapper = mount(RulesTree, {
      props: { groups: [], records: [rule('r1')] },
    });

    expect(wrapper.text()).toContain('r1');
    expect(wrapper.find('.apqa-rules-tree-group').exists()).toBe(false);
  });

  it('renders folder aliases as name: chain when expanded', async () => {
    const wrapper = mount(RulesTree, {
      props: {
        groups: [
          group('Data', '', [
            { name: 'survey_mdd', chain: [{ cmdlet: 'get-content-mdd', args: { path: 'x' } }] },
          ]),
        ],
        records: [],
      },
    });

    expect(wrapper.text()).not.toContain('survey_mdd');

    await wrapper.find('.apqa-rules-tree-group-header').trigger('click');

    expect(wrapper.text()).toContain('survey_mdd');
    expect(wrapper.text()).toContain('get-content-mdd');
    expect(wrapper.text()).toContain('path=x');
  });

  it('keeps child rules hidden while a parent folder is folded', async () => {
    const wrapper = mount(RulesTree, {
      props: {
        groups: [group('Data'), group('Metadata', 'Data')],
        records: [rule('r1', 'Metadata')],
      },
    });

    // Everything starts folded: only the top-level folder heading is visible.
    expect(wrapper.text()).toContain('Data');
    expect(wrapper.text()).toContain('[+]');
    expect(wrapper.text()).not.toContain('Metadata');
    expect(wrapper.text()).not.toContain('r1');

    // Expand Data -> the Metadata folder heading appears (still folded).
    await wrapper.find('.apqa-rules-tree-group-header').trigger('click');
    expect(wrapper.text()).toContain('Metadata');
    expect(wrapper.text()).not.toContain('r1');

    // Expand Metadata -> the rule appears.
    const headers = wrapper.findAll('.apqa-rules-tree-group-header');
    await headers[1].trigger('click');
    expect(wrapper.text()).toContain('r1');
  });

  it('paginates the visible node list', async () => {
    const wrapper = mount(RulesTree, {
      props: {
        groups: [],
        records: [rule('r1'), rule('r2')],
        recordsPerPage: 1,
      },
    });

    expect(wrapper.text()).toContain('r1');
    expect(wrapper.text()).not.toContain('r2');
    const pages = wrapper.findAll('.apqa-rules-tree-page');
    expect(pages).toHaveLength(2);

    await pages[1].trigger('click');
    expect(wrapper.text()).toContain('r2');
    expect(wrapper.text()).not.toContain('r1');
  });

  it('forwards delete actions from an expanded rule', async () => {
    const wrapper = mount(RulesTree, {
      props: { groups: [], records: [rule('r1')] },
    });
    await wrapper.find('.apqa-rule-compact-description').trigger('click');
    await wrapper.find('.apqa-rule-body-action-delete').trigger('click');

    expect(wrapper.emitted('delete')).toHaveLength(1);
    expect(wrapper.emitted('delete')[0][0]).toMatchObject({ name: 'r1' });
  });

  it('assigns mark classes to rule leaves', () => {
    const wrapper = mount(RulesTree, {
      props: { groups: [], records: [rule('r1', '', { markers: ['skip'] })] },
    });

    const li = wrapper.find('li.apqa-rule-record');
    expect(li.classes()).toContain('apqa-rules-tree-item');
    expect(li.classes()).toContain('skip');
  });

  it('aggregates rule mark classes onto a folder heading', () => {
    const wrapper = mount(RulesTree, {
      props: {
        groups: [group('Data')],
        records: [rule('r1', 'Data', { markers: ['skip'] })],
      },
    });

    const folder = wrapper.find('.apqa-rules-tree-group');
    expect(folder.classes()).toContain('apqa-rules-tree-item');
    expect(folder.classes()).toContain('skip');
  });

  it('shows a folder mark summary with aggregated badges', () => {
    const wrapper = mount(RulesTree, {
      props: {
        groups: [group('Data')],
        records: [rule('r1', 'Data', { markers: ['skip'] })],
      },
    });

    const summary = wrapper.find('.apqa-rules-tree-group-marks');
    expect(summary.text()).toContain('includes rules marked');
    const badges = summary.findAll('.apqa-mark-badge');
    expect(badges.map((badge) => badge.text())).toEqual(['skip', 'unfinished']);
  });

  it('refuses to collapse a folder that contains the rule being edited', async () => {
    const wrapper = mount(RulesTree, {
      props: {
        groups: [group('Data')],
        records: [rule('r1', 'Data')],
      },
      global: { components: { 'component-input-cmdlet-chain': ChainStub } },
    });

    await wrapper.find('.apqa-rules-tree-group-header').trigger('click');
    expect(wrapper.text()).toContain('r1');

    await wrapper.setProps({ editingId: 'r1' });
    const alert = vi.spyOn(window, 'alert').mockImplementation(() => {});

    await wrapper.find('.apqa-rules-tree-group-header').trigger('click');

    // The folder stays expanded and the edit form is not destroyed.
    expect(wrapper.find('input[name="name"]').element.value).toBe('r1');
    expect(wrapper.text()).toContain('[-]');
    expect(alert).toHaveBeenCalled();

    alert.mockRestore();
  });

  it('refuses to change page while a rule is being edited', async () => {
    const alert = vi.spyOn(window, 'alert').mockImplementation(() => {});
    const wrapper = mount(RulesTree, {
      props: {
        groups: [],
        records: [rule('r1'), rule('r2')],
        recordsPerPage: 1,
        editingId: 'r1',
      },
      global: { components: { 'component-input-cmdlet-chain': ChainStub } },
    });

    await wrapper.findAll('.apqa-rules-tree-page')[1].trigger('click');

    // The edited rule's form stays mounted; the page does not change to r2.
    expect(wrapper.find('input[name="name"]').element.value).toBe('r1');
    expect(wrapper.find('.apqa-rule-edit-form').exists()).toBe(true);
    expect(alert).toHaveBeenCalled();

    alert.mockRestore();
  });

  it('forwards save and cancel from an editing rule', async () => {
    const wrapper = mount(RulesTree, {
      props: {
        groups: [],
        records: [rule('r1')],
        editingId: 'r1',
      },
      global: { components: { 'component-input-cmdlet-chain': ChainStub } },
    });

    await wrapper.find('input[name="name"]').setValue('renamed');
    await wrapper.find('form').trigger('submit');

    expect(wrapper.emitted('save')).toHaveLength(1);
    expect(wrapper.emitted('save')[0][0]).toMatchObject({ name: 'r1' });
    expect(wrapper.emitted('save')[0][1]).toMatchObject({ name: 'renamed' });

    await wrapper.find('.apqa-rule-form-button').trigger('click');
    expect(wrapper.emitted('cancel')).toHaveLength(1);
  });

});

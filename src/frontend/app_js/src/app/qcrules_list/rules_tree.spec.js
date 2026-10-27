import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';

import RulesTree from './rules_tree.js';

function rule(name, group = '') {
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
  };
}

function group(name, parent = '', aliases = []) {
  return { id: name, name, parent, aliases };
}

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
});

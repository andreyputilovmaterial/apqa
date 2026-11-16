import { describe, it, expect, vi } from 'vitest';
import { mount } from '@vue/test-utils';

import RulesTree from './rules_tree.js';
import { cmdletComponents } from '@/common_components/cmdlet_components/index.js';
import { inputCmdletComponents } from '@/common_components/input_types/cmdlets/index.js';

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

function group(name, parent = '', aliases = [], comment = '', extra = {}) {
  return { id: name, name, parent, aliases, comment, tags: [], markers: [], ...extra };
}

// `rules_tree` renders cmdlets through the globally-registered display
// components and the edit form through the editing components; register both
// for every mount (same sets as app.js).
const GLOBAL_COMPONENTS = {
  ...cmdletComponents,
  ...inputCmdletComponents,
};

function mountTree(options = {}) {
  return mount(RulesTree, {
    ...options,
    global: {
      components: { ...GLOBAL_COMPONENTS, ...options.global?.components },
    },
  });
}

describe('RulesTree', () => {
  it('starts with folders folded and expands on click', async () => {
    const wrapper = mountTree({
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

  it('keeps folders expanded when the groups prop reloads with the same ids (reorder)', async () => {
    const wrapper = mountTree({
      props: { groups: [group('data')], records: [rule('r1', 'data')] },
    });

    await wrapper.find('.apqa-rules-tree-group-header').trigger('click');
    expect(wrapper.text()).toContain('r1');

    // The page reloads groups + records after a reorder POST.
    await wrapper.setProps({
      groups: [group('data')],
      records: [rule('r1', 'data')],
    });

    expect(wrapper.text()).toContain('r1');
    expect(wrapper.text()).toContain('[-]');
  });

  it('folds a newly added folder while leaving existing folders untouched', async () => {
    const wrapper = mountTree({
      props: { groups: [group('data')], records: [rule('r1', 'data')] },
    });

    await wrapper.find('.apqa-rules-tree-group-header').trigger('click');
    expect(wrapper.text()).toContain('r1');

    await wrapper.setProps({
      groups: [group('data'), group('extra')],
      records: [rule('r1', 'data')],
    });

    // data stays expanded; the new extra folder starts folded.
    expect(wrapper.text()).toContain('r1');
    expect(wrapper.find('[data-node-key="g:extra"] .apqa-rules-tree-group-toggle').text()).toBe('[+]');
  });

  it('keeps the rule card rendered when the records prop reloads with the same id', async () => {
    const wrapper = mountTree({
      props: { groups: [], records: [rule('r1')] },
    });

    expect(wrapper.find('[data-node-key="r:r1"] .apqa-rule-card').exists()).toBe(true);

    await wrapper.setProps({ records: [rule('r1')] });

    expect(wrapper.find('[data-node-key="r:r1"] .apqa-rule-card').exists()).toBe(true);
  });

  it('renders ungrouped rules directly, without a folder heading', () => {
    const wrapper = mountTree({
      props: { groups: [], records: [rule('r1')] },
    });

    expect(wrapper.text()).toContain('r1');
    expect(wrapper.find('.apqa-rules-tree-group').exists()).toBe(false);
  });

  it('renders folder aliases as name: chain when expanded', async () => {
    const wrapper = mountTree({
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

  it('renders the folder comment next to the name', async () => {
    const wrapper = mountTree({
      props: { groups: [group('Data', '', [], 'Wave 69 checks')], records: [] },
    });

    expect(wrapper.find('.apqa-rules-tree-group-comment').text()).toBe('Wave 69 checks');
  });

  it('keeps child rules hidden while a parent folder is folded', async () => {
    const wrapper = mountTree({
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
    const wrapper = mountTree({
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

  it('forwards delete actions from a rule', async () => {
    const wrapper = mountTree({
      props: { groups: [], records: [rule('r1')] },
    });
    await wrapper.find('.apqa-record-action-delete').trigger('click');

    expect(wrapper.emitted('delete')).toHaveLength(1);
    expect(wrapper.emitted('delete')[0][0]).toMatchObject({ name: 'r1' });
  });

  it('forwards edit-group, run-group and delete-group actions from a folder', async () => {
    const wrapper = mountTree({
      props: { groups: [group('Data')], records: [] },
    });

    await wrapper.find('.apqa-record-action-edit').trigger('click');
    await wrapper.find('.apqa-record-action-run').trigger('click');
    await wrapper.find('.apqa-record-action-delete').trigger('click');

    expect(wrapper.emitted('edit-group')).toHaveLength(1);
    expect(wrapper.emitted('edit-group')[0][0]).toMatchObject({ id: 'Data', name: 'Data' });
    expect(wrapper.emitted('run-group')).toHaveLength(1);
    expect(wrapper.emitted('run-group')[0][0]).toMatchObject({ id: 'Data', name: 'Data' });
    expect(wrapper.emitted('delete-group')).toHaveLength(1);
    expect(wrapper.emitted('delete-group')[0][0]).toMatchObject({ id: 'Data', name: 'Data' });
  });

  it("shows a folder's own tags and markers in its meta row", () => {
    const wrapper = mountTree({
      props: {
        groups: [group('Data', '', [], '', { tags: ['counts'], markers: ['skip'] })],
        records: [],
      },
    });

    const meta = wrapper.find('.apqa-rules-tree-group .apqa-record-meta');
    expect(meta.find('.apqa-record-tags').text()).toBe('counts');
    expect(meta.find('.apqa-mark-badge').text()).toBe('skip');
  });

  it('assigns mark classes to rule leaves', () => {
    const wrapper = mountTree({
      props: { groups: [], records: [rule('r1', '', { markers: ['skip'] })] },
    });

    const li = wrapper.find('li.apqa-rule-record');
    expect(li.classes()).toContain('apqa-rules-tree-item');
    expect(li.classes()).toContain('skip');
  });

  it('aggregates rule mark classes onto a folder heading', () => {
    const wrapper = mountTree({
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
    const wrapper = mountTree({
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
    const wrapper = mountTree({
      props: {
        groups: [group('Data')],
        records: [rule('r1', 'Data')],
      },
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
    const wrapper = mountTree({
      props: {
        groups: [],
        records: [rule('r1'), rule('r2')],
        recordsPerPage: 1,
        editingId: 'r1',
      },
    });

    await wrapper.findAll('.apqa-rules-tree-page')[1].trigger('click');

    // The edited rule's form stays mounted; the page does not change to r2.
    expect(wrapper.find('input[name="name"]').element.value).toBe('r1');
    expect(wrapper.find('.apqa-rule-edit-form').exists()).toBe(true);
    expect(alert).toHaveBeenCalled();

    alert.mockRestore();
  });

  it('forwards save and cancel from an editing rule', async () => {
    const wrapper = mountTree({
      props: {
        groups: [],
        records: [rule('r1')],
        editingId: 'r1',
      },
    });

    await wrapper.find('input[name="name"]').setValue('renamed');
    await wrapper.find('form').trigger('submit');

    expect(wrapper.emitted('save')).toHaveLength(1);
    expect(wrapper.emitted('save')[0][0]).toMatchObject({ name: 'r1' });
    expect(wrapper.emitted('save')[0][1]).toMatchObject({ name: 'renamed' });

    await wrapper.find('.apqa-rule-form-button').trigger('click');
    expect(wrapper.emitted('cancel')).toHaveLength(1);
  });

  it('shows a passed folder tick when every rule inside passed', () => {
    const wrapper = mountTree({
      props: {
        groups: [group('Data')],
        records: [rule('r1', 'Data'), rule('r2', 'Data')],
        runResults: { r1: { status: 'passed' }, r2: { status: 'passed' } },
      },
    });

    const tick = wrapper.find('.apqa-rules-tree-group .apqa-rule-run-tick');
    expect(tick.exists()).toBe(true);
    expect(tick.classes()).toContain('is-passed');
    expect(tick.find('i.ri-check-double-line').exists()).toBe(true);
  });

  it('shows a blank folder tick when nothing inside has run', () => {
    const wrapper = mountTree({
      props: {
        groups: [group('Data')],
        records: [rule('r1', 'Data'), rule('r2', 'Data')],
      },
    });

    const tick = wrapper.find('.apqa-rules-tree-group .apqa-rule-run-tick');
    expect(tick.exists()).toBe(true);
    expect(tick.classes()).toContain('is-empty');
    expect(tick.find('i').exists()).toBe(false);
    expect(tick.find('.apqa-run-tick-text').exists()).toBe(false);
  });

  it('shows a failed folder tick when any rule inside failed', () => {
    const wrapper = mountTree({
      props: {
        groups: [group('Data')],
        records: [rule('r1', 'Data'), rule('r2', 'Data')],
        runResults: { r1: { status: 'passed' }, r2: { status: 'failed' } },
      },
    });

    const tick = wrapper.find('.apqa-rules-tree-group .apqa-rule-run-tick');
    expect(tick.classes()).toContain('is-failed');
    expect(tick.find('i.ri-close-fill').exists()).toBe(true);
  });

  it('shows a running folder tick when a rule inside is running', () => {
    const wrapper = mountTree({
      props: {
        groups: [group('Data')],
        records: [rule('r1', 'Data')],
        runResults: { r1: { status: 'running' } },
      },
    });

    const tick = wrapper.find('.apqa-rules-tree-group .apqa-rule-run-tick');
    expect(tick.classes()).toContain('is-running');
    expect(tick.find('i.ri-loader-4-line').exists()).toBe(true);
  });

  it('shows an indeterminate folder tick when not all rules inside passed', () => {
    const wrapper = mountTree({
      props: {
        groups: [group('Data')],
        records: [rule('r1', 'Data'), rule('r2', 'Data')],
        runResults: { r1: { status: 'passed' } },
      },
    });

    const tick = wrapper.find('.apqa-rules-tree-group .apqa-rule-run-tick');
    expect(tick.classes()).toContain('is-indeterminate');
    expect(tick.find('.apqa-run-tick-text').text()).toBe('±');
  });

  it('shows no folder tick for a folder with no rules inside', () => {
    const wrapper = mountTree({
      props: { groups: [group('Empty')], records: [] },
    });

    expect(wrapper.find('.apqa-rules-tree-group .apqa-rule-run-tick').exists()).toBe(false);
  });

  it('emits reorder when a rule is dragged below another and dropped', async () => {
    const wrapper = mountTree({
      props: { groups: [], records: [rule('r1'), rule('r2')] },
    });

    // Start dragging r1 from its header (desktop pointer: drag starts on move).
    await wrapper.find('[data-node-key="r:r1"] .apqa-rule-card-head').trigger('pointerdown');

    // Move below every row, then release on the window (the tree listens globally).
    const move = new Event('pointermove');
    move.clientY = 100;
    window.dispatchEvent(move);
    window.dispatchEvent(new Event('pointerup'));

    expect(wrapper.emitted('reorder')).toHaveLength(1);
    expect(wrapper.emitted('reorder')[0][0]).toEqual({
      kind: 'rule',
      id: 'r1',
      parent: '',
      before: null,
    });
  });

  it('emits reorder when a folder header is dragged below another row and dropped', async () => {
    const wrapper = mountTree({
      props: { groups: [group('data')], records: [rule('r1', 'data'), rule('r2', '', { order: 1 })] },
    });

    await wrapper.find('[data-node-key="g:data"] .apqa-rules-tree-group-header').trigger('pointerdown');

    const move = new Event('pointermove');
    move.clientY = 100;
    window.dispatchEvent(move);
    window.dispatchEvent(new Event('pointerup'));

    expect(wrapper.emitted('reorder')).toHaveLength(1);
    expect(wrapper.emitted('reorder')[0][0]).toEqual({
      kind: 'group',
      id: 'data',
      parent: '',
      before: null,
    });
  });

  it('does not emit reorder on a plain rule-header click (no drag)', async () => {
    const wrapper = mountTree({
      props: { groups: [], records: [rule('r1')] },
    });

    await wrapper.find('[data-node-key="r:r1"] .apqa-rule-card-head').trigger('click');

    expect(wrapper.find('[data-node-key="r:r1"] .apqa-rule-card').exists()).toBe(true);
    expect(wrapper.emitted('reorder')).toBeUndefined();
  });

  it('swallows the click after a rule header drag', async () => {
    const wrapper = mountTree({
      props: { groups: [], records: [rule('r1'), rule('r2')] },
    });

    await wrapper.find('[data-node-key="r:r1"] .apqa-rule-card-head').trigger('pointerdown');

    const move = new Event('pointermove');
    move.clientY = 100;
    window.dispatchEvent(move);
    window.dispatchEvent(new Event('pointerup'));

    await wrapper.find('[data-node-key="r:r1"] .apqa-rule-card-head').trigger('click');

    expect(wrapper.emitted('reorder')).toHaveLength(1);
    // The swallowed click must not have changed the rule card.
    expect(wrapper.find('[data-node-key="r:r1"] .apqa-rule-card').exists()).toBe(true);
  });

});

import { describe, it, expect, vi, afterEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';

import { createModal } from '@/common_components/modals/modals';
import QcRulesList from './index.js';
import RulesTree from './rules_tree.js';
import { cmdletComponents } from '@/common_components/cmdlet_components/index.js';

vi.mock('@/common_components/modals/modals', () => ({
  createModal: vi.fn(),
}));

// `QcRulesList` loads rules + groups in its `onMounted` hook and renders the
// rules tree from the loaded records. Stub `fetch` so the page renders
// records without a backend.
function stubFetch(rules, groups = []) {
  vi.stubGlobal(
    'fetch',
    vi.fn((url) => {
      const body = url === '/qc/rules' ? { rules } : url === '/qc/groups' ? { groups } : { rules: [] };
      return Promise.resolve({ ok: true, json: () => Promise.resolve(body) });
    }),
  );
}

describe('QcRulesList', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    createModal.mockReset();
  });

  it('passes distinct tag suggestions down to the rules tree', async () => {
    stubFetch(
      [
        { id: 'r1', name: 'Rule one', left: [], op: '', right: [], meta: { tags: ['counts', 'wave69'] } },
        { id: 'r2', name: 'Rule two', left: [], op: '', right: [], meta: { tags: ['wave69'] } },
      ],
      [{ id: 'g1', name: 'Group', parent: '', meta: { tags: ['folder-tag'] } }],
    );

    const wrapper = mount(QcRulesList, { global: { components: cmdletComponents } });
    await flushPromises();

    const tree = wrapper.findComponent(RulesTree);
    expect(tree.exists()).toBe(true);
    expect(tree.props('tagSuggestions')).toEqual(['counts', 'folder-tag', 'wave69']);
  });

  it('runs a rule on Run click and shows the cached failed result', async () => {
    const rule = {
      id: 'r1',
      name: 'Rule one',
      group: '',
      left: [],
      op: 'eq',
      op_args: {},
      right: [],
      meta: {},
    };

    vi.stubGlobal('fetch', vi.fn((url) => {
      if (url === '/qc/rules') return Promise.resolve({ ok: true, json: () => Promise.resolve({ rules: [rule] }) });
      if (url === '/qc/groups') return Promise.resolve({ ok: true, json: () => Promise.resolve({ groups: [] }) });
      if (url === '/cmdlets/metadata') return Promise.resolve({ ok: true, json: () => Promise.resolve({ cmdlets: [], ops: [] }) });
      if (url === '/tests/run') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            result: false,
            notes: [{ path: ['Fields', 'A', 'Label'], message: 'not XML-compatible' }],
          }),
        });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    }));

    const wrapper = mount(QcRulesList, { global: { components: cmdletComponents } });
    await flushPromises();

    await wrapper.find('.apqa-record-action-run').trigger('click');
    await flushPromises();

    expect(wrapper.find('.apqa-rule-run-result .apqa-rule-run-result-failed').text()).toBe('Failed');
    expect(wrapper.find('.apqa-rule-run-result-notes li').text()).toContain(
      'Fields.A.Label: not XML-compatible',
    );
  });

  it('runs every rule in a folder sequentially when run-group fires', async () => {
    const rules = [
      { id: 'r1', name: 'Rule one', group: 'data', left: [], op: 'eq', op_args: {}, right: [], meta: { order: 1 } },
      { id: 'r2', name: 'Rule two', group: 'data', left: [], op: 'eq', op_args: {}, right: [], meta: { order: 2 } },
    ];
    const group = { id: 'data', name: 'Data', parent: '', meta: {} };

    const runOrder = [];
    vi.stubGlobal('fetch', vi.fn((url, options = {}) => {
      if (url === '/qc/rules') return Promise.resolve({ ok: true, json: () => Promise.resolve({ rules }) });
      if (url === '/qc/groups') return Promise.resolve({ ok: true, json: () => Promise.resolve({ groups: [group] }) });
      if (url === '/cmdlets/metadata') return Promise.resolve({ ok: true, json: () => Promise.resolve({ cmdlets: [], ops: [] }) });
      if (url === '/tests/run') {
        runOrder.push(JSON.parse(options.body).id);
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ result: true }) });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    }));

    const wrapper = mount(QcRulesList, { global: { components: cmdletComponents } });
    await flushPromises();

    wrapper.findComponent(RulesTree).vm.$emit('run-group', { id: 'data', name: 'Data' });

    await vi.waitFor(() => {
      expect(runOrder).toEqual(['r1', 'r2']);
    });
  });

  it('shows a "no tests ran" note instead of an alert when running an empty folder', async () => {
    const rule = { id: 'r1', name: 'Rule one', group: '', left: [], op: 'eq', op_args: {}, right: [], meta: {} };
    const group = { id: 'empty', name: 'Empty', parent: '', meta: {} };

    const alert = vi.spyOn(window, 'alert').mockImplementation(() => {});

    vi.stubGlobal('fetch', vi.fn((url) => {
      if (url === '/qc/rules') return Promise.resolve({ ok: true, json: () => Promise.resolve({ rules: [rule] }) });
      if (url === '/qc/groups') return Promise.resolve({ ok: true, json: () => Promise.resolve({ groups: [group] }) });
      if (url === '/cmdlets/metadata') return Promise.resolve({ ok: true, json: () => Promise.resolve({ cmdlets: [], ops: [] }) });
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    }));

    const wrapper = mount(QcRulesList, { global: { components: cmdletComponents } });
    await flushPromises();

    wrapper.findComponent(RulesTree).vm.$emit('run-group', { id: 'empty', name: 'Empty' });
    await flushPromises();

    expect(alert).not.toHaveBeenCalled();
    expect(wrapper.find('.apqa-rules-tree-group-run-result-status').text()).toBe('no tests ran');

    alert.mockRestore();
  });

  it('keeps a folder expanded across a reorder reload', async () => {
    const rule = { id: 'r1', name: 'Rule one', group: 'data', left: [], op: '', right: [], meta: {} };
    const group = { id: 'data', name: 'Data', parent: '', meta: {} };

    vi.stubGlobal('fetch', vi.fn((url) => {
      if (url === '/qc/reorder') return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
      if (url === '/qc/rules') return Promise.resolve({ ok: true, json: () => Promise.resolve({ rules: [rule] }) });
      if (url === '/qc/groups') return Promise.resolve({ ok: true, json: () => Promise.resolve({ groups: [group] }) });
      if (url === '/cmdlets/metadata') return Promise.resolve({ ok: true, json: () => Promise.resolve({ cmdlets: [], ops: [] }) });
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    }));

    const wrapper = mount(QcRulesList, { global: { components: cmdletComponents } });
    await flushPromises();

    await wrapper.find('.apqa-rules-tree-group-header').trigger('click');
    expect(wrapper.text()).toContain('Rule one');

    // A reorder reloads rules + groups; the tree must not remount and re-fold.
    wrapper.findComponent(RulesTree).vm.$emit('reorder', {
      kind: 'rule',
      id: 'r1',
      parent: 'data',
      before: null,
    });
    await flushPromises();

    expect(wrapper.text()).toContain('Rule one');
  });

  it('duplicates a rule and reloads the list', async () => {
    const rule = { id: 'r1', name: 'Rule one', group: '', left: [], op: '', right: [], meta: {} };

    const calls = [];
    vi.stubGlobal('fetch', vi.fn((url, options = {}) => {
      calls.push({ url, method: options.method || 'GET' });
      if (url === '/qc/rules') return Promise.resolve({ ok: true, json: () => Promise.resolve({ rules: [rule] }) });
      if (url === '/qc/groups') return Promise.resolve({ ok: true, json: () => Promise.resolve({ groups: [] }) });
      if (url === '/cmdlets/metadata') return Promise.resolve({ ok: true, json: () => Promise.resolve({ cmdlets: [], ops: [] }) });
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    }));

    const wrapper = mount(QcRulesList, { global: { components: cmdletComponents } });
    await flushPromises();

    wrapper.findComponent(RulesTree).vm.$emit('duplicate', { id: 'r1', name: 'Rule one' });
    await flushPromises();

    expect(calls).toContainEqual({ url: '/qc/rules/r1/duplicate', method: 'POST' });
  });

  it('shows a red exception snippet when running raises', async () => {
    const rule = {
      id: 'r1',
      name: 'Rule one',
      group: '',
      left: [],
      op: 'eq',
      op_args: {},
      right: [],
      meta: {},
    };

    vi.stubGlobal('fetch', vi.fn((url) => {
      if (url === '/qc/rules') return Promise.resolve({ ok: true, json: () => Promise.resolve({ rules: [rule] }) });
      if (url === '/qc/groups') return Promise.resolve({ ok: true, json: () => Promise.resolve({ groups: [] }) });
      if (url === '/cmdlets/metadata') return Promise.resolve({ ok: true, json: () => Promise.resolve({ cmdlets: [], ops: [] }) });
      if (url === '/tests/run') {
        return Promise.resolve({
          ok: false,
          status: 400,
          json: () => Promise.resolve({ error: "cmdlet 'nope' (step 0): cmdlet not found: nope" }),
        });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    }));

    const wrapper = mount(QcRulesList, { global: { components: cmdletComponents } });
    await flushPromises();

    await wrapper.find('.apqa-record-action-run').trigger('click');
    await flushPromises();

    expect(wrapper.find('.apqa-rule-run-result-error').text()).toBe(
      "cmdlet 'nope' (step 0): cmdlet not found: nope",
    );
  });

  it('shows a "View full trace" action and opens a modal for an error with a traceback', async () => {
    const rule = {
      id: 'r1',
      name: 'Rule one',
      group: '',
      left: [],
      op: 'eq',
      op_args: {},
      right: [],
      meta: {},
    };

    vi.stubGlobal('fetch', vi.fn((url) => {
      if (url === '/qc/rules') return Promise.resolve({ ok: true, json: () => Promise.resolve({ rules: [rule] }) });
      if (url === '/qc/groups') return Promise.resolve({ ok: true, json: () => Promise.resolve({ groups: [] }) });
      if (url === '/cmdlets/metadata') return Promise.resolve({ ok: true, json: () => Promise.resolve({ cmdlets: [], ops: [] }) });
      if (url === '/tests/run') {
        return Promise.resolve({
          ok: false,
          status: 400,
          json: () => Promise.resolve({
            error: "cmdlet 'get-content-mdd' (step 0): boom",
            traceback: 'Traceback (most recent call last):\n  boom',
          }),
        });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    }));

    const wrapper = mount(QcRulesList, { global: { components: cmdletComponents } });
    await flushPromises();

    await wrapper.find('.apqa-record-action-run').trigger('click');
    await flushPromises();

    expect(wrapper.find('.apqa-rule-run-result-error').text()).toBe(
      "cmdlet 'get-content-mdd' (step 0): boom",
    );
    const traceButton = wrapper.find('.apqa-rule-run-result-error-trace');
    expect(traceButton.exists()).toBe(true);

    await traceButton.trigger('click');
    expect(createModal).toHaveBeenCalledTimes(1);
  });

  it('edits a folder and PUTs the updated fields', async () => {
    const group = {
      id: 'data',
      name: 'Data',
      parent: '',
      meta: { comment: 'old', tags: ['wave'] },
    };
    const rule = { id: 'r1', name: 'Rule one', group: 'data', left: [], op: '', right: [], meta: {} };

    let putPayload = null;
    vi.stubGlobal(
      'fetch',
      vi.fn((url, options = {}) => {
        const method = options.method || 'GET';
        if (url === '/qc/rules') return Promise.resolve({ ok: true, json: () => Promise.resolve({ rules: [rule] }) });
        if (url === '/qc/groups' && method === 'GET') return Promise.resolve({ ok: true, json: () => Promise.resolve({ groups: [group] }) });
        if (url === '/qc/groups/data' && method === 'PUT') {
          putPayload = JSON.parse(options.body);
          return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
        }
        if (url === '/cmdlets/metadata') return Promise.resolve({ ok: true, json: () => Promise.resolve({ cmdlets: [], ops: [] }) });
        return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
      }),
    );

    const wrapper = mount(QcRulesList, { global: { components: cmdletComponents } });
    await flushPromises();

    wrapper.findComponent(RulesTree).vm.$emit('edit-group', {
      id: 'data',
      name: 'Data',
      comment: 'old',
      tags: ['wave'],
    });
    await flushPromises();

    const editForm = wrapper.find('.apqa-group-edit-form');
    expect(editForm.exists()).toBe(true);

    await editForm.find('input[name="name"]').setValue('Data v2');
    await editForm.find('form').trigger('submit');
    await flushPromises();

    expect(putPayload).toMatchObject({ name: 'Data v2', parent: '' });
    expect(putPayload.meta).toEqual({ comment: 'old', tags: ['wave'] });
  });

  it('renders intro copy and icon actions instead of the old toolbar buttons', async () => {
    stubFetch([]);

    const wrapper = mount(QcRulesList, { global: { components: cmdletComponents } });
    await flushPromises();

    expect(wrapper.find('.apqa-qcrules-page-toolbar').exists()).toBe(false);
    expect(wrapper.find('.apqa-qcrules-page-intro').exists()).toBe(true);
    expect(wrapper.find('.apqa-qcrules-page-intro').text()).toContain('Define QC tests once and reuse them across projects');
    expect(wrapper.find('.apqa-qcrules-page-intro').text()).toContain('Run tests manually or automatically');
    expect(wrapper.find('.apqa-record-action-create-rule i.ri-add-large-fill').exists()).toBe(true);
    expect(wrapper.find('.apqa-record-action-create-folder i.ri-folder-add-line').exists()).toBe(true);
    expect(wrapper.find('.apqa-record-action-run-all i.ri-play-large-line').exists()).toBe(true);
  });

  it('runs all rules in tree order on run-all click and shows the summary', async () => {
    const rules = [
      { id: 'r-ungrouped', name: 'Ungrouped', group: '', left: [], op: 'eq', op_args: {}, right: [], meta: { order: 0 } },
      { id: 'r-a', name: 'Rule A', group: 'a', left: [], op: 'eq', op_args: {}, right: [], meta: { order: 1 } },
      { id: 'r-a1', name: 'Rule A1', group: 'a1', left: [], op: 'eq', op_args: {}, right: [], meta: { order: 0 } },
      { id: 'r-b', name: 'Rule B', group: 'b', left: [], op: 'eq', op_args: {}, right: [], meta: { order: 0 } },
    ];
    const groups = [
      { id: 'a', name: 'A', parent: '', meta: { order: 1 } },
      { id: 'a1', name: 'A-1', parent: 'a', meta: { order: 0 } },
      { id: 'b', name: 'B', parent: '', meta: { order: 2 } },
    ];

    const runOrder = [];
    vi.stubGlobal('fetch', vi.fn((url, options = {}) => {
      if (url === '/qc/rules') return Promise.resolve({ ok: true, json: () => Promise.resolve({ rules }) });
      if (url === '/qc/groups') return Promise.resolve({ ok: true, json: () => Promise.resolve({ groups }) });
      if (url === '/cmdlets/metadata') return Promise.resolve({ ok: true, json: () => Promise.resolve({ cmdlets: [], ops: [] }) });
      if (url === '/tests/run') {
        runOrder.push(JSON.parse(options.body).id);
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ result: true }) });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    }));

    const wrapper = mount(QcRulesList, { global: { components: cmdletComponents } });
    await flushPromises();

    await wrapper.find('.apqa-record-action-run-all').trigger('click');

    await vi.waitFor(() => {
      expect(runOrder).toEqual(['r-ungrouped', 'r-a1', 'r-a', 'r-b']);
    });

    expect(wrapper.find('.apqa-qcrules-page-all-run-result-status').text()).toBe('4 passed');
  });

  it('shows a "no tests ran" note when run-all is clicked with no rules', async () => {
    stubFetch([]);

    const wrapper = mount(QcRulesList, { global: { components: cmdletComponents } });
    await flushPromises();

    await wrapper.find('.apqa-record-action-run-all').trigger('click');
    await flushPromises();

    expect(wrapper.find('.apqa-qcrules-page-all-run-result-status').text()).toBe('no tests ran');
  });

  it('creates a subfolder with the clicked parent and last-child order on add-subfolder', async () => {
    const rules = [
      { id: 'r1', name: 'Rule one', group: 'data', left: [], op: '', right: [], meta: { order: 2 } },
    ];
    const groups = [
      { id: 'data', name: 'Data', parent: '', meta: { order: 5 } },
      { id: 'other', name: 'Other', parent: '', meta: {} },
    ];

    createModal.mockResolvedValueOnce({ name: 'Sub', parent: '' });

    let posted = null;
    vi.stubGlobal('fetch', vi.fn((url, options = {}) => {
      const method = options.method || 'GET';
      if (url === '/qc/rules') return Promise.resolve({ ok: true, json: () => Promise.resolve({ rules }) });
      if (url === '/qc/groups' && method === 'GET') return Promise.resolve({ ok: true, json: () => Promise.resolve({ groups }) });
      if (url === '/qc/groups' && method === 'POST') {
        posted = JSON.parse(options.body);
        return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
      }
      if (url === '/cmdlets/metadata') return Promise.resolve({ ok: true, json: () => Promise.resolve({ cmdlets: [], ops: [] }) });
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    }));

    const wrapper = mount(QcRulesList, { global: { components: cmdletComponents } });
    await flushPromises();

    wrapper.findComponent(RulesTree).vm.$emit('add-subfolder', { id: 'data', name: 'Data' });
    await flushPromises();

    expect(posted).toMatchObject({ name: 'Sub', parent: 'data' });
    expect(posted.meta).toEqual({ order: 3 });
  });
});

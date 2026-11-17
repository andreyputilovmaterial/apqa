import { describe, it, expect, vi, afterEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';

import QcRulesList from './index.js';
import RulesTree from './rules_tree.js';
import { cmdletComponents } from '@/common_components/cmdlet_components/index.js';

// `QcRulesList` loads rules + groups in its `onMounted` hook and renders the
// `records-filter` -> `rules-tree` pipeline. Stub `fetch` so the page renders
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
      if (url === '/functionality/cmdlet-metadata') return Promise.resolve({ ok: true, json: () => Promise.resolve({ cmdlets: [], ops: [] }) });
      if (url === '/functionality/run-rule') {
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

    expect(wrapper.find('.apqa-rule-run-result-failed').text()).toBe('Failed');
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
      if (url === '/functionality/cmdlet-metadata') return Promise.resolve({ ok: true, json: () => Promise.resolve({ cmdlets: [], ops: [] }) });
      if (url === '/functionality/run-rule') {
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
      if (url === '/functionality/cmdlet-metadata') return Promise.resolve({ ok: true, json: () => Promise.resolve({ cmdlets: [], ops: [] }) });
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
      if (url === '/functionality/cmdlet-metadata') return Promise.resolve({ ok: true, json: () => Promise.resolve({ cmdlets: [], ops: [] }) });
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
      if (url === '/functionality/cmdlet-metadata') return Promise.resolve({ ok: true, json: () => Promise.resolve({ cmdlets: [], ops: [] }) });
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
      if (url === '/functionality/cmdlet-metadata') return Promise.resolve({ ok: true, json: () => Promise.resolve({ cmdlets: [], ops: [] }) });
      if (url === '/functionality/run-rule') {
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
        if (url === '/functionality/cmdlet-metadata') return Promise.resolve({ ok: true, json: () => Promise.resolve({ cmdlets: [], ops: [] }) });
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
      markers: [],
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
});

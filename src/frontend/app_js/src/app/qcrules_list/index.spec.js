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
    stubFetch([
      { id: 'r1', name: 'Rule one', left: [], op: '', right: [], meta: { tags: ['counts', 'wave69'] } },
      { id: 'r2', name: 'Rule two', left: [], op: '', right: [], meta: { tags: ['wave69'] } },
    ]);

    const wrapper = mount(QcRulesList, { global: { components: cmdletComponents } });
    await flushPromises();

    const tree = wrapper.findComponent(RulesTree);
    expect(tree.exists()).toBe(true);
    expect(tree.props('tagSuggestions')).toEqual(['counts', 'wave69']);
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
            notes: [{ path: ['fields', 'A', 'label'], message: 'not XML-compatible' }],
          }),
        });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    }));

    const wrapper = mount(QcRulesList, { global: { components: cmdletComponents } });
    await flushPromises();

    await wrapper.find('.apqa-rule-compact-description').trigger('click');
    await wrapper.find('.apqa-rule-body-action-run').trigger('click');
    await flushPromises();

    expect(wrapper.find('.apqa-rule-run-result-failed').text()).toBe('Failed');
    expect(wrapper.find('.apqa-rule-run-result-notes li').text()).toContain(
      'fields.A.label: not XML-compatible',
    );
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

    await wrapper.find('.apqa-rule-compact-description').trigger('click');
    await wrapper.find('.apqa-rule-body-action-run').trigger('click');
    await flushPromises();

    expect(wrapper.find('.apqa-rule-run-result-error').text()).toBe(
      "cmdlet 'nope' (step 0): cmdlet not found: nope",
    );
  });
});

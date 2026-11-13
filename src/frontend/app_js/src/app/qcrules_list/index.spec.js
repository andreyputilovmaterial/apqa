import { describe, it, expect, vi, afterEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';

import QcRulesList from './index.js';
import RulesTree from './rules_tree.js';

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

    const wrapper = mount(QcRulesList);
    await flushPromises();

    const tree = wrapper.findComponent(RulesTree);
    expect(tree.exists()).toBe(true);
    expect(tree.props('tagSuggestions')).toEqual(['counts', 'wave69']);
  });
});

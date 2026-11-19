import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import CmdletChainCompact from './compact.js';
import { cmdletComponents } from '@/common_components/cmdlet_components/index.js';

const CMDLETS = [
  { name: 'get-content', kind: 'source', args: [{ name: 'path', type: 'path' }] },
  { name: 'count', kind: 'processor', args: [] },
];

function mountChain(chain) {
  return mount(CmdletChainCompact, {
    global: { components: cmdletComponents },
    props: { chain, cmdlets: CMDLETS },
  });
}

describe('cmdlet-chain compact', () => {
  it('separates adjacent chips with a tab character in the text', () => {
    const wrapper = mountChain([
      { cmdlet: 'get-content', args: { path: 'a.sav' } },
      { cmdlet: 'count' },
    ]);

    expect(wrapper.text()).toBe('get-content path=a.sav\tcount');
  });

  it('adds no separator for a single chip or an empty chain', () => {
    expect(mountChain([{ cmdlet: 'count' }]).text()).toBe('count');
    expect(mountChain([]).text()).toBe('(empty)');
  });
});

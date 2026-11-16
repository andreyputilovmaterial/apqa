import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import Compact from './compact.js';
import { cmdletComponents } from '@/common_components/cmdlet_components/index.js';

const CMDLETS = [
  { name: 'get-content', kind: 'source', args: [{ name: 'path', type: 'path' }] },
];

function mountChains(value) {
  return mount(Compact, {
    global: { components: cmdletComponents },
    props: { value, cmdlets: CMDLETS },
  });
}

describe('cmdlet-chains compact', () => {
  it('renders each nested chain separated by a comma', () => {
    const wrapper = mountChains([
      [{ cmdlet: 'get-content', args: { path: 'a.sav' } }],
      [{ cmdlet: 'get-content', args: { path: 'b.sav' } }],
    ]);

    expect(wrapper.text()).toContain('get-content path=a.sav');
    expect(wrapper.text()).toContain(', ');
    expect(wrapper.text()).toContain('get-content path=b.sav');
  });

  it('renders nothing for an empty or missing list', () => {
    expect(mountChains([]).text()).toBe('');
    expect(mountChains(null).text()).toBe('');
  });
});

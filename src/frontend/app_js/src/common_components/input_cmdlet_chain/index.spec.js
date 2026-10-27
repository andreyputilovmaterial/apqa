import { describe, it, expect } from 'vitest';
import { defineComponent, ref } from 'vue';
import { mount } from '@vue/test-utils';
import InputCmdletChain from './index.js';

const CMDLETS = [
  { name: 'get-content-excel', kind: 'source', args: [] },
  { name: 'count', kind: 'processor', args: [] },
];

const Harness = defineComponent({
  components: { 'input-cmdlet-chain': InputCmdletChain },
  props: ['cmdlets'],
  template: `<input-cmdlet-chain v-model="chain" :cmdlets="cmdlets" />`,
  setup() {
    const chain = ref([]);
    return { chain };
  },
});

const ChainStub = { template: '<div class="chain-stub" />' };
const GLOBAL = { components: { 'component-input-cmdlet-chain': ChainStub } };

function mountChain(props = {}) {
  return mount(InputCmdletChain, {
    props: { cmdlets: CMDLETS, ...props },
    global: GLOBAL,
  });
}

function mountHarness() {
  return mount(Harness, { props: { cmdlets: CMDLETS }, global: GLOBAL });
}

describe('InputCmdletChain', () => {
  it('renders a single source placeholder when empty', () => {
    const wrapper = mountChain();
    const triggers = wrapper.findAll('.apqa-input-search-select-trigger');
    expect(triggers).toHaveLength(1);
    expect(triggers[0].text()).toContain('source');
  });

  it('offers only source readers in the first slot', async () => {
    const wrapper = mountChain();
    await wrapper.find('.apqa-input-search-select-trigger').trigger('click');
    const options = wrapper.findAll('.apqa-input-search-select-option');
    expect(options.map((o) => o.text())).toEqual(['get-content-excel']);
  });

  it('shows a new placeholder after the first cmdlet is selected', async () => {
    const wrapper = mountHarness();
    await wrapper.find('.apqa-input-search-select-trigger').trigger('click');
    const first = wrapper
      .findAll('.apqa-input-search-select-option')
      .find((o) => o.text() === 'get-content-excel');
    await first.trigger('click');

    expect(wrapper.findAll('.apqa-input-cmdlet-selected')).toHaveLength(1);
    const triggers = wrapper.findAll('.apqa-input-search-select-trigger');
    expect(triggers).toHaveLength(1);
    // The new placeholder must stay empty, not pre-select the next candidate.
    expect(triggers[0].text()).toContain('Select next cmdlet');
    await triggers[0].trigger('click');
    const options = wrapper.findAll('.apqa-input-search-select-option');
    expect(options.map((o) => o.text())).toEqual(['count']);
  });
});

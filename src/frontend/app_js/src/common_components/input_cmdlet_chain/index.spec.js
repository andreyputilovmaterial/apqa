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
    const selects = wrapper.findAll('select.apqa-input-cmdlet-select');
    expect(selects).toHaveLength(1);
    expect(selects[0].find('option[disabled]').text()).toContain('source');
  });

  it('offers only source readers in the first slot', () => {
    const wrapper = mountChain();
    const options = wrapper
      .findAll('select.apqa-input-cmdlet-select option')
      .filter((o) => o.attributes('value'));
    expect(options.map((o) => o.text())).toEqual(['get-content-excel']);
  });

  it('shows a new placeholder after the first cmdlet is selected', async () => {
    const wrapper = mountHarness();
    await wrapper.find('select.apqa-input-cmdlet-select').setValue('get-content-excel');

    expect(wrapper.findAll('.apqa-input-cmdlet-selected')).toHaveLength(1);
    const selects = wrapper.findAll('select.apqa-input-cmdlet-select');
    expect(selects).toHaveLength(1);
    // The new placeholder must stay blank, not pre-select the next candidate.
    expect(selects[0].element.value).toBe('');
    const options = selects[0]
      .findAll('option')
      .filter((o) => o.attributes('value'));
    expect(options.map((o) => o.text())).toEqual(['count']);
  });
});

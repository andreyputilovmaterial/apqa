import { describe, it, expect } from 'vitest';
import { flushPromises, mount } from '@vue/test-utils';
import InputCmdlet from './index.js';

const CMDLETS = [
  { name: 'literal', kind: 'source', args: [{ name: 'value', type: 'json', required: true }] },
  { name: 'count', kind: 'processor', args: [{ name: 'fail_on_sysmissing', type: 'boolean', default: false }] },
  { name: 'matches', kind: 'processor', args: [{ name: 'pattern', type: 'text', required: true }] },
];

// `input_cmdlet` references the chain component by its global name for the
// `cmdlet-chains` arg type (to avoid a circular import); register a stub so the
// template resolves in isolation.
const ChainStub = { template: '<div class="chain-stub" />' };

function mountCmdlet(props = {}) {
  return mount(InputCmdlet, {
    props: { cmdlets: CMDLETS, ...props },
    global: { components: { 'component-input-cmdlet-chain': ChainStub } },
  });
}

describe('InputCmdlet', () => {
  it('renders a searchable drop down when nothing is selected', () => {
    const wrapper = mountCmdlet();
    const trigger = wrapper.find('.apqa-input-search-select-trigger');
    expect(trigger.exists()).toBe(true);
    expect(trigger.text()).toContain('Select cmdlet');
  });

  it('focuses the search box when the drop down opens', async () => {
    const wrapper = mount(InputCmdlet, {
      attachTo: document.body,
      props: { cmdlets: CMDLETS },
      global: { components: { 'component-input-cmdlet-chain': ChainStub } },
    });
    await wrapper.find('.apqa-input-search-select-trigger').trigger('click');
    await flushPromises();
    expect(document.activeElement).toBe(
      wrapper.find('.apqa-input-search-select-search').element,
    );
    wrapper.unmount();
  });

  it('filters the drop down by kind', async () => {
    const wrapper = mountCmdlet({ kinds: ['source'] });
    await wrapper.find('.apqa-input-search-select-trigger').trigger('click');
    const options = wrapper.findAll('.apqa-input-search-select-option');
    expect(options.map((o) => o.text())).toEqual(['literal']);
  });

  it('emits the chosen cmdlet as the model value', async () => {
    const wrapper = mountCmdlet();
    await wrapper.find('.apqa-input-search-select-trigger').trigger('click');
    const option = wrapper
      .findAll('.apqa-input-search-select-option')
      .find((o) => o.text() === 'count');
    await option.trigger('click');
    expect(wrapper.emitted('update:modelValue').at(-1)).toEqual([
      { cmdlet: 'count', args: {} },
    ]);
  });

  it('renders one input per argument once selected', () => {
    const wrapper = mountCmdlet({ modelValue: { cmdlet: 'matches', args: {} } });
    expect(wrapper.find('input[name="pattern"]').exists()).toBe(true);
  });

  it('emits an updated args mapping when an argument changes', async () => {
    const wrapper = mountCmdlet({ modelValue: { cmdlet: 'matches', args: {} } });
    await wrapper.find('input[name="pattern"]').setValue('abc');
    expect(wrapper.emitted('update:modelValue').at(-1)).toEqual([
      { cmdlet: 'matches', args: { pattern: 'abc' } },
    ]);
  });
});

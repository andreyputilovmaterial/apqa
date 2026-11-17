import { describe, it, expect } from 'vitest';
import { flushPromises, mount } from '@vue/test-utils';
import InputCmdlet from './index.js';
import { inputCmdletComponents } from '../index.js';

const CMDLETS = [
  { name: 'literal', kind: 'source', args: [{ name: 'value', type: 'literal-value', required: true }] },
  { name: 'count', kind: 'processor', args: [{ name: 'fail_on_sysmissing', type: 'boolean', default: false }] },
  { name: 'validate-text-matches', kind: 'terminal', args: [{ name: 'pattern', type: 'text', required: true }] },
  { name: 'map', kind: 'processor', args: [{ name: 'transform', type: 'cmdlet-chain', required: true }] },
];

// `input_cmdlet` renders its arguments through the globally-registered arg
// editors (and nested chains through the chain editor); register the full
// editing set for the mount, as app.js does.
function mountCmdlet(props = {}) {
  return mount(InputCmdlet, {
    props: { cmdlets: CMDLETS, ...props },
    global: { components: inputCmdletComponents },
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
      global: { components: inputCmdletComponents },
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
    const wrapper = mountCmdlet({ modelValue: { cmdlet: 'validate-text-matches', args: {} } });
    expect(wrapper.find('input[name="pattern"]').exists()).toBe(true);
  });

  it('emits an updated args mapping when an argument changes', async () => {
    const wrapper = mountCmdlet({ modelValue: { cmdlet: 'validate-text-matches', args: {} } });
    await wrapper.find('input[name="pattern"]').setValue('abc');
    expect(wrapper.emitted('update:modelValue').at(-1)).toEqual([
      { cmdlet: 'validate-text-matches', args: { pattern: 'abc' } },
    ]);
  });

  it('renders a single chain for a cmdlet-chain arg', () => {
    const wrapper = mountCmdlet({ modelValue: { cmdlet: 'map', args: {} } });
    expect(wrapper.find('.apqa-input-cmdlet-arg-chain').exists()).toBe(true);
    expect(wrapper.find('.apqa-input-cmdlet-arg-chain .apqa-input-cmdlet-chain').exists()).toBe(true);
  });
});

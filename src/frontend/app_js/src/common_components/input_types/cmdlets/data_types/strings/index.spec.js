import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import InputArgStrings from './index.js';

function mountStrings(value = []) {
  return mount(InputArgStrings, { props: { value } });
}

describe('InputArgStrings', () => {
  it('renders one text input per value', () => {
    const wrapper = mountStrings(['a', 'b']);
    const inputs = wrapper.findAll('input[type="text"]');
    expect(inputs).toHaveLength(2);
    expect(inputs.map((i) => i.element.value)).toEqual(['a', 'b']);
  });

  it('adds an empty value', async () => {
    const wrapper = mountStrings(['a']);
    await wrapper.find('.apqa-input-cmdlet-arg-add-string').trigger('click');
    expect(wrapper.emitted('update:value')[0][0]).toEqual(['a', '']);
  });

  it('removes the chosen value', async () => {
    const wrapper = mountStrings(['a', 'b']);
    await wrapper.findAll('.apqa-input-cmdlet-arg-string-remove')[0].trigger('click');
    expect(wrapper.emitted('update:value')[0][0]).toEqual(['b']);
  });

  it('updates a value on input', async () => {
    const wrapper = mountStrings(['a', 'b']);
    await wrapper.findAll('input[type="text"]')[0].setValue('changed');
    expect(wrapper.emitted('update:value')[0][0]).toEqual(['changed', 'b']);
  });
});

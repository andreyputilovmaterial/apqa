import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import InputRegexText from './index.js';

function mountComponent(props = {}, attrs = {}) {
  return mount(InputRegexText, { props, attrs });
}

describe('InputRegexText', () => {
  it('renders a text input and the .* toggle', () => {
    const wrapper = mountComponent();
    expect(wrapper.find('input.apqa-input-regex-text-input').exists()).toBe(true);
    expect(wrapper.find('.apqa-input-regex-text-toggle').text()).toBe('.*');
  });

  it('emits { text, regex:false } on input', async () => {
    const wrapper = mountComponent();
    await wrapper.find('input').setValue('foo');
    expect(wrapper.emitted('input')[0][0].target.value).toEqual({ text: 'foo', regex: false });
    expect(wrapper.emitted('update:modelValue')[0][0]).toEqual({ text: 'foo', regex: false });
  });

  it('toggles regex mode and emits the new value', async () => {
    const wrapper = mountComponent();
    const toggle = wrapper.find('.apqa-input-regex-text-toggle');

    await toggle.trigger('click');
    expect(toggle.classes()).toContain('is-active');
    expect(wrapper.emitted('update:modelValue')[0][0]).toEqual({ text: '', regex: true });

    await toggle.trigger('click');
    expect(toggle.classes()).not.toContain('is-active');
    expect(wrapper.emitted('update:modelValue')[1][0]).toEqual({ text: '', regex: false });
  });

  it('starts with regex on when regexDefault is true', async () => {
    const wrapper = mountComponent({ regexDefault: true });
    expect(wrapper.find('.apqa-input-regex-text-toggle').classes()).toContain('is-active');

    await wrapper.find('input').setValue('file.*');
    expect(wrapper.emitted('update:modelValue')[0][0]).toEqual({ text: 'file.*', regex: true });
  });

  it('passes name and placeholder through to the inner input', () => {
    const wrapper = mountComponent({}, { name: 'filter-name', placeholder: 'Filter...' });
    const input = wrapper.find('input');
    expect(input.attributes('name')).toBe('filter-name');
    expect(input.attributes('placeholder')).toBe('Filter...');
  });
});

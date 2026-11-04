import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import FormField from './index.js';

describe('FormField', () => {
  it('renders label, help and slotted content', () => {
    const wrapper = mount(FormField, {
      props: { label: 'Name', help: 'Full name', required: true },
      slots: { default: '<input type="text" />' },
    });
    expect(wrapper.find('.apqa-form-field-label-text').text()).toContain('Name');
    expect(wrapper.find('.apqa-form-field-help').text()).toBe('Full name');
    expect(wrapper.find('input[type="text"]').exists()).toBe(true);
    expect(wrapper.find('.apqa-form-field-required-mark').exists()).toBe(true);
  });

  it('applies the left label position class', () => {
    const wrapper = mount(FormField, {
      props: { label: 'Name', labelPosition: 'left' },
      slots: { default: '<input type="text" />' },
    });
    expect(wrapper.find('.apqa-form-field-label-left').exists()).toBe(true);
  });
});

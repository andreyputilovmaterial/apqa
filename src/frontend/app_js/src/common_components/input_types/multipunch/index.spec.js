import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import InputMultipunch from './index.js';

function mountComponent(props = {}) {
  return mount(InputMultipunch, {
    props: {
      options: ['counts', 'wave69'],
      placeholder: 'Filter tags...',
      ...props,
    },
  });
}

describe('InputMultipunch', () => {
  it('shows the placeholder and keeps the menu closed when nothing is selected', () => {
    const wrapper = mountComponent();
    expect(wrapper.find('.apqa-input-multipunch-trigger').text()).toContain('Filter tags...');
    expect(wrapper.find('.apqa-input-multipunch-menu').exists()).toBe(false);
  });

  it('opens and lists the options when the trigger is clicked', async () => {
    const wrapper = mountComponent();
    await wrapper.find('.apqa-input-multipunch-trigger').trigger('click');

    const menu = wrapper.find('.apqa-input-multipunch-menu');
    expect(menu.exists()).toBe(true);
    expect(menu.findAll('.apqa-input-multipunch-option')).toHaveLength(2);
  });

  it('toggles an option into the model value', async () => {
    const wrapper = mountComponent();
    await wrapper.find('.apqa-input-multipunch-trigger').trigger('click');

    await wrapper.find('input[type="checkbox"][value="counts"]').setValue(true);
    expect(wrapper.emitted('update:modelValue').at(-1)).toEqual([['counts']]);
  });

  it('shows the selected values on the trigger', () => {
    const wrapper = mountComponent({ modelValue: ['counts'] });
    expect(wrapper.find('.apqa-input-multipunch-trigger').text()).toContain('counts');
  });

  it('closes when clicking outside the component', async () => {
    const wrapper = mountComponent();
    await wrapper.find('.apqa-input-multipunch-trigger').trigger('click');
    expect(wrapper.find('.apqa-input-multipunch-menu').exists()).toBe(true);

    const outside = document.createElement('div');
    document.body.appendChild(outside);
    await outside.dispatchEvent(new Event('pointerdown', { bubbles: true }));

    expect(wrapper.find('.apqa-input-multipunch-menu').exists()).toBe(false);
    outside.remove();
  });
});

import { describe, it, expect } from 'vitest';
import { flushPromises, mount } from '@vue/test-utils';
import SearchSelect from './index.js';

function mountComponent(props = {}) {
  return mount(SearchSelect, {
    props: {
      options: ['count', 'matches', 'literal'],
      placeholder: 'Select cmdlet…',
      ...props,
    },
  });
}

describe('SearchSelect', () => {
  it('shows the placeholder and keeps the menu closed when nothing is selected', () => {
    const wrapper = mountComponent();
    expect(wrapper.find('.apqa-search-select-trigger').text()).toContain('Select cmdlet…');
    expect(wrapper.find('.apqa-search-select-menu').exists()).toBe(false);
  });

  it('opens and focuses the search box when the trigger is clicked', async () => {
    const wrapper = mount(SearchSelect, {
      attachTo: document.body,
      props: { options: ['count', 'matches', 'literal'], placeholder: 'Select cmdlet…' },
    });
    await wrapper.find('.apqa-search-select-trigger').trigger('click');
    await flushPromises();

    expect(wrapper.find('.apqa-search-select-menu').exists()).toBe(true);
    expect(document.activeElement).toBe(wrapper.find('.apqa-search-select-search').element);
    wrapper.unmount();
  });

  it('filters the options by the search text', async () => {
    const wrapper = mountComponent();
    await wrapper.find('.apqa-search-select-trigger').trigger('click');

    await wrapper.find('.apqa-search-select-search').setValue('mat');
    const options = wrapper.findAll('.apqa-search-select-option');
    expect(options.map((o) => o.text())).toEqual(['matches']);
  });

  it('emits the chosen value and closes the menu', async () => {
    const wrapper = mountComponent();
    await wrapper.find('.apqa-search-select-trigger').trigger('click');

    const option = wrapper
      .findAll('.apqa-search-select-option')
      .find((o) => o.text() === 'count');
    await option.trigger('click');

    expect(wrapper.emitted('update:modelValue').at(-1)).toEqual(['count']);
    expect(wrapper.find('.apqa-search-select-menu').exists()).toBe(false);
  });

  it('shows the selected label on the trigger', () => {
    const wrapper = mountComponent({ modelValue: 'count' });
    expect(wrapper.find('.apqa-search-select-trigger').text()).toContain('count');
  });

  it('closes when clicking outside the component', async () => {
    const wrapper = mountComponent();
    await wrapper.find('.apqa-search-select-trigger').trigger('click');
    expect(wrapper.find('.apqa-search-select-menu').exists()).toBe(true);

    const outside = document.createElement('div');
    document.body.appendChild(outside);
    await outside.dispatchEvent(new Event('pointerdown', { bubbles: true }));

    expect(wrapper.find('.apqa-search-select-menu').exists()).toBe(false);
    outside.remove();
  });
});

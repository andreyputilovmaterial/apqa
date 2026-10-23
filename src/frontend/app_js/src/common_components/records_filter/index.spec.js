import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import RecordsFilter from './index.js';

const columns = {
  name: { label: 'Name', type: 'text' },
  comment: { label: 'Comment', type: 'text' },
};

const records = [
  { id: 'a', name: 'Alps', comment: 'hiking' },
  { id: 'b', name: 'Japan', comment: 'trip' },
];

function mountFilter(props = {}) {
  return mount(RecordsFilter, {
    props: {
      columns,
      records,
      keyField: 'id',
      ...props,
    },
  });
}

describe('RecordsFilter', () => {
  it('starts collapsed and expands/collapses on header click', async () => {
    const wrapper = mountFilter();
    const header = wrapper.find('.apqa-records-filter-header');

    expect(header.exists()).toBe(true);
    expect(wrapper.find('.apqa-records-filter-form').exists()).toBe(false);
    expect(wrapper.find('.apqa-records-filter-toolbar').exists()).toBe(false);

    await header.trigger('click');
    expect(wrapper.find('.apqa-records-filter-form').exists()).toBe(true);
    expect(wrapper.find('.apqa-records-filter-toolbar').exists()).toBe(true);

    await wrapper.find('.apqa-records-filter-header').trigger('click');
    expect(wrapper.find('.apqa-records-filter-form').exists()).toBe(false);
    expect(wrapper.find('.apqa-records-filter-toolbar').exists()).toBe(false);
  });

  it('shows a summary of the active filter in both collapsed and expanded states', async () => {
    const wrapper = mountFilter();

    await wrapper.find('.apqa-records-filter-header').trigger('click');
    await wrapper.find('input[name="filter-name"]').setValue('alp');

    let header = wrapper.find('.apqa-records-filter-header');
    expect(header.text()).toContain('Name: alp');
    expect(header.find('.apqa-records-filter-header-summary').exists()).toBe(true);

    await wrapper.find('.apqa-records-filter-header').trigger('click');
    header = wrapper.find('.apqa-records-filter-header');
    expect(header.text()).toContain('Name: alp');
    expect(header.find('.apqa-records-filter-header-summary').exists()).toBe(true);
  });

  it('shows no summary when nothing is filtered', async () => {
    const wrapper = mountFilter();
    const header = wrapper.find('.apqa-records-filter-header');

    expect(header.find('.apqa-records-filter-header-summary').exists()).toBe(false);
    expect(header.text()).toContain('Filter');
  });
});

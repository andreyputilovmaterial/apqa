import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';

import GroupEditForm from './group_edit_form.js';

function makeGroup(overrides = {}) {
  return {
    id: 'data',
    name: 'Data checks',
    comment: 'Rules about data',
    tags: ['counts'],
    markers: ['skip'],
    ...overrides,
  };
}

function mountForm(props = {}) {
  return mount(GroupEditForm, {
    props: {
      group: makeGroup(),
      collapsed: false,
      tagSuggestions: ['counts', 'wave69'],
      ...props,
    },
  });
}

describe('GroupEditForm', () => {
  it('prefills the editable fields from the group', () => {
    const wrapper = mountForm();

    expect(wrapper.find('input[name="name"]').element.value).toBe('Data checks');
    expect(wrapper.find('input[name="comment"]').element.value).toBe('Rules about data');
  });

  it('mirrors the folder header (name, comment, toggle) above the fields', () => {
    const wrapper = mountForm();

    expect(wrapper.find('.apqa-rules-tree-group-name').text()).toBe('Data checks');
    expect(wrapper.find('.apqa-rules-tree-group-comment').text()).toBe('Rules about data');
    expect(wrapper.find('.apqa-rules-tree-group-toggle').text()).toBe('[-]');

    const collapsed = mountForm({ collapsed: true });
    expect(collapsed.find('.apqa-rules-tree-group-toggle').text()).toBe('[+]');
  });

  it('shows the save/cancel icon action row', () => {
    const wrapper = mountForm();

    expect(wrapper.find('.apqa-record-action-save i.ri-save-3-line').exists()).toBe(true);
    expect(wrapper.find('.apqa-record-action-cancel i.ri-close-circle-line').exists()).toBe(true);
  });

  it('emits the edited fields on save', async () => {
    const wrapper = mountForm();
    await wrapper.find('input[name="name"]').setValue('Renamed checks');
    await wrapper.find('form').trigger('submit');

    expect(wrapper.emitted('save')).toHaveLength(1);
    expect(wrapper.emitted('save')[0][0]).toEqual({
      name: 'Renamed checks',
      comment: 'Rules about data',
      tags: ['counts'],
      markers: ['skip'],
    });
  });

  it('does not emit save when the name is empty', async () => {
    const wrapper = mountForm();
    await wrapper.find('input[name="name"]').setValue('');
    await wrapper.find('form').trigger('submit');

    expect(wrapper.emitted('save')).toBeUndefined();
    expect(wrapper.find('.apqa-group-form-error').text()).toContain('Name is required');
  });

  it('emits cancel when the close button is clicked', async () => {
    const wrapper = mountForm();
    await wrapper.find('.apqa-group-form-button').trigger('click');

    expect(wrapper.emitted('cancel')).toHaveLength(1);
  });
});

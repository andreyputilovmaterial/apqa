import { describe, it, expect, vi } from 'vitest';
import { mount } from '@vue/test-utils';

import GroupForm from './group_form.js';

function mountForm(props = {}) {
  return mount(GroupForm, {
    props: { resolve: vi.fn(), reject: vi.fn(), ...props },
  });
}

describe('GroupForm', () => {
  it('resolves name + comment in the payload on submit', async () => {
    const resolve = vi.fn();
    const wrapper = mountForm({ resolve });

    await wrapper.find('input[name="name"]').setValue('Data checks');
    await wrapper.find('input[name="comment"]').setValue('Rules about data');
    await wrapper.find('form').trigger('submit');

    expect(resolve).toHaveBeenCalledTimes(1);
    const payload = resolve.mock.calls[0][0];
    expect(payload.name).toBe('Data checks');
    expect(payload.parent).toBe('');
    expect(payload.meta).toEqual({ comment: 'Rules about data' });
  });

  it('does not resolve when the name is empty', async () => {
    const resolve = vi.fn();
    const wrapper = mountForm({ resolve });

    await wrapper.find('form').trigger('submit');

    expect(resolve).not.toHaveBeenCalled();
    expect(wrapper.find('.apqa-group-form-error').text()).toBe('Name is required.');
  });

  it('omits meta when the comment is empty', async () => {
    const resolve = vi.fn();
    const wrapper = mountForm({ resolve });

    await wrapper.find('input[name="name"]').setValue('Data checks');
    await wrapper.find('form').trigger('submit');

    expect(resolve).toHaveBeenCalledTimes(1);
    expect(resolve.mock.calls[0][0]).toEqual({ name: 'Data checks', parent: '' });
  });
});

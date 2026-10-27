import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import RuleEditForm from './rule_edit_form.js';

// `input_cmdlet` references the chain component by its global name for the
// `cmdlet-chains` arg type (to avoid a circular import); register a stub so the
// form mounts without global registration.
const ChainStub = { template: '<div class="chain-stub" />' };

function makeRecord(overrides = {}) {
  return {
    id: 'wave-69',
    name: 'Wave 69',
    comment: 'check the count',
    tags: ['counts'],
    markers: ['skip'],
    left: [{ cmdlet: 'get-content', args: { path: 'a.sav' } }],
    op: 'eq',
    op_args: { unordered_arrays: true },
    right: [{ cmdlet: 'count' }],
    ...overrides,
  };
}

function mountForm(props = {}) {
  return mount(RuleEditForm, {
    props: { record: makeRecord(), cmdlets: [], ops: [], tagSuggestions: [], ...props },
    global: { components: { 'component-input-cmdlet-chain': ChainStub } },
  });
}

describe('RuleEditForm', () => {
  it('prefills the editable fields from the record', () => {
    const wrapper = mountForm();

    expect((wrapper.find('input[name="name"]').element).value).toBe('Wave 69');
    expect((wrapper.find('input[name="comment"]').element).value).toBe('check the count');
    expect((wrapper.find('input[name="id"]').element).value).toBe('wave-69');
    expect(wrapper.find('input[name="id"]').attributes('disabled')).toBeDefined();
  });

  it('emits the edited fields on save', async () => {
    const wrapper = mountForm();
    await wrapper.find('input[name="name"]').setValue('Wave 69 counts');
    await wrapper.find('form').trigger('submit');

    expect(wrapper.emitted('save')).toHaveLength(1);
    expect(wrapper.emitted('save')[0][0]).toEqual({
      name: 'Wave 69 counts',
      comment: 'check the count',
      tags: ['counts'],
      markers: ['skip'],
      left: [{ cmdlet: 'get-content', args: { path: 'a.sav' } }],
      op: 'eq',
      op_args: { unordered_arrays: true },
      right: [{ cmdlet: 'count' }],
    });
  });

  it('does not emit save when the name is empty', async () => {
    const wrapper = mountForm();
    await wrapper.find('input[name="name"]').setValue('');
    await wrapper.find('form').trigger('submit');

    expect(wrapper.emitted('save')).toBeUndefined();
    expect(wrapper.find('.apqa-rule-form-error').text()).toContain('Name is required');
  });

  it('emits cancel when the cancel button is clicked', async () => {
    const wrapper = mountForm();
    await wrapper.find('.apqa-rule-form-button').trigger('click');

    expect(wrapper.emitted('cancel')).toHaveLength(1);
  });
});

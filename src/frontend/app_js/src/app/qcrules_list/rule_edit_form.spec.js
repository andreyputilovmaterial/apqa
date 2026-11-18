import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import RuleEditForm from './rule_edit_form.js';
import { inputCmdletComponents } from '@/common_components/input_types/cmdlets/index.js';

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

// The form renders the cmdlet chain and comparison op through the globally-
// registered editing components; register the full editing set for the mount.
function mountForm(props = {}) {
  return mount(RuleEditForm, {
    props: { record: makeRecord(), cmdlets: [], ops: [], tagSuggestions: [], ...props },
    global: { components: inputCmdletComponents },
  });
}

describe('RuleEditForm', () => {
  it('prefills the editable fields from the record', async () => {
    const wrapper = mountForm();
    await wrapper.find('.apqa-rule-form-id-toggle').trigger('click');

    expect((wrapper.find('input[name="name"]').element).value).toBe('Wave 69');
    expect((wrapper.find('input[name="comment"]').element).value).toBe('check the count');
    expect((wrapper.find('input[name="id"]').element).value).toBe('wave-69');
    expect(wrapper.find('input[name="id"]').attributes('disabled')).toBeDefined();
  });

  it('shows the read-only QC rule ID collapsed above the name and expands on click', async () => {
    const wrapper = mountForm();

    const toggle = wrapper.find('.apqa-rule-form-id-toggle');
    expect(toggle.find('.ri-arrow-down-double-fill').exists()).toBe(true);
    expect(toggle.find('.ri-arrow-up-double-fill').exists()).toBe(false);
    expect(toggle.find('.apqa-rule-form-id-value').text()).toBe('wave-69');
    expect(wrapper.find('input[name="id"]').exists()).toBe(false);

    const html = wrapper.html();
    expect(html.indexOf('apqa-rule-form-id-toggle')).toBeLessThan(html.indexOf('name="name"'));

    await toggle.trigger('click');

    expect(wrapper.find('.ri-arrow-up-double-fill').exists()).toBe(true);
    expect(wrapper.find('.ri-arrow-down-double-fill').exists()).toBe(false);
    expect(wrapper.find('.apqa-rule-form-id-editor .apqa-rule-form-field-label').text()).toBe('QC rule ID');

    const idInput = wrapper.find('input[name="id"]');
    expect(idInput.exists()).toBe(true);
    expect(idInput.attributes('disabled')).toBeDefined();
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

  it('mirrors the rule header and shows the save/cancel icon row above the fields', () => {
    const wrapper = mountForm();

    expect(wrapper.find('.apqa-rule-card-name').text()).toBe('Wave 69');
    expect(wrapper.find('.apqa-rule-card-comment').text()).toBe('check the count');
    expect(wrapper.find('.apqa-record-action-save i.ri-save-3-line').exists()).toBe(true);
    expect(wrapper.find('.apqa-record-action-cancel i.ri-close-circle-line').exists()).toBe(true);

    // Cancel is the left-most icon, so a repeated click on the same spot as
    // Edit cancels instead of saving.
    const html = wrapper.html();
    expect(html.indexOf('apqa-record-action-cancel')).toBeLessThan(html.indexOf('apqa-record-action-save'));
  });

  it('shows full-size Save and Close buttons at the bottom', () => {
    const wrapper = mountForm();
    const buttons = wrapper.findAll('.apqa-rule-form-actions .apqa-rule-form-button');

    expect(buttons.map((button) => button.text().trim())).toEqual(['Close', 'Save']);
  });
});

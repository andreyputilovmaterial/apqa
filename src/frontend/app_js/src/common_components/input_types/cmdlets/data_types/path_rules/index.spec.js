import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import InputArgPathRules from './index.js';

function mountRules(value = []) {
  return mount(InputArgPathRules, { props: { value } });
}

describe('InputArgPathRules', () => {
  it('renders one rule row per value', () => {
    const wrapper = mountRules([
      { name: 'Skip Select', type: 'eq', pattern: 'Fields.Select', case_insensitive: false },
    ]);
    expect(wrapper.findAll('.apqa-input-cmdlet-arg-path-rule')).toHaveLength(1);
    expect(wrapper.find('.apqa-input-cmdlet-arg-rule-pattern').element.value).toBe('Fields.Select');
  });

  it('adds an empty rule', async () => {
    const wrapper = mountRules([]);
    await wrapper.find('.apqa-input-cmdlet-arg-add-string').trigger('click');
    expect(wrapper.emitted('update:value')[0][0]).toEqual([
      { name: '', type: 'eq', pattern: '', case_insensitive: false },
    ]);
  });

  it('removes the chosen rule', async () => {
    const wrapper = mountRules([
      { name: '', type: 'eq', pattern: 'a', case_insensitive: false },
      { name: '', type: 'eq', pattern: 'b', case_insensitive: false },
    ]);
    await wrapper.findAll('.apqa-input-cmdlet-arg-string-remove')[0].trigger('click');
    expect(wrapper.emitted('update:value')[0][0]).toEqual([
      { name: '', type: 'eq', pattern: 'b', case_insensitive: false },
    ]);
  });

  it('updates a pattern on input', async () => {
    const wrapper = mountRules([
      { name: '', type: 'eq', pattern: 'a', case_insensitive: false },
    ]);
    await wrapper.find('.apqa-input-cmdlet-arg-rule-pattern').setValue('b');
    expect(wrapper.emitted('update:value')[0][0][0].pattern).toBe('b');
  });

  it('updates the match type on change', async () => {
    const wrapper = mountRules([
      { name: '', type: 'eq', pattern: 'a', case_insensitive: false },
    ]);
    await wrapper.find('select').setValue('regex');
    expect(wrapper.emitted('update:value')[0][0][0].type).toBe('regex');
  });

  it('toggles the case-insensitive flag', async () => {
    const wrapper = mountRules([
      { name: '', type: 'eq', pattern: 'a', case_insensitive: false },
    ]);
    await wrapper.find('input[type="checkbox"]').setValue(true);
    expect(wrapper.emitted('update:value')[0][0][0].case_insensitive).toBe(true);
  });
});

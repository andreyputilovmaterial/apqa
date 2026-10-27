import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import InputQcruleMarks from './index.js';

describe('InputQcruleMarks', () => {
  it('renders the supported markers as multi-punch options', async () => {
    const wrapper = mount(InputQcruleMarks, { props: { modelValue: [] } });
    await wrapper.find('.apqa-multipunch-trigger').trigger('click');
    const labels = wrapper.findAll('.apqa-multipunch-option-label').map((el) => el.text());
    expect(labels).toEqual(['skip', 'xfail']);
  });

  it('forwards a toggled marker as the model value', async () => {
    const wrapper = mount(InputQcruleMarks, { props: { modelValue: [] } });
    await wrapper.find('.apqa-multipunch-trigger').trigger('click');
    await wrapper.find('input[type="checkbox"][value="skip"]').setValue(true);
    expect(wrapper.emitted('update:modelValue').at(-1)).toEqual([['skip']]);
  });
});

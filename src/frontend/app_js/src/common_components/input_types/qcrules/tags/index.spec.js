import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import InputQcruleTags from './index.js';

function mountTags(props = {}) {
  return mount(InputQcruleTags, { props: { ...props } });
}

describe('InputQcruleTags', () => {
  it('commits a typed tag on Enter', async () => {
    const wrapper = mountTags();
    const input = wrapper.find('input.apqa-input-qcrule-tags-input');
    await input.setValue('counts');
    await input.trigger('keydown', { key: 'Enter' });

    expect(wrapper.emitted('update:modelValue').at(-1)).toEqual([['counts']]);
    expect(input.element.value).toBe('');
  });

  it('removes a tag when its remove button is clicked', async () => {
    const wrapper = mountTags({ modelValue: ['counts', 'wave69'] });
    await wrapper.find('.apqa-input-qcrule-tags-remove').trigger('click');
    expect(wrapper.emitted('update:modelValue').at(-1)).toEqual([['wave69']]);
  });
});

import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import InputGallery from './index.js';

function mountGallery() {
  return mount(InputGallery);
}

describe('InputGallery', () => {
  it('renders a section for every input family', () => {
    const wrapper = mountGallery();
    const titles = wrapper.findAll('.apqa-input-gallery-section-title').map((t) => t.text());
    expect(titles).toContain('Text inputs');
    expect(titles).toContain('Numbers');
    expect(titles).toContain('Date & time');
    expect(titles).toContain('Ranges');
    expect(titles).toContain('File picker');
    expect(titles).toContain('Selects');
    expect(titles).toContain('Checkboxes');
    expect(titles).toContain('Radio buttons');
    expect(titles).toContain('Buttons');
  });

  it('renders the reusable range and select components', () => {
    const wrapper = mountGallery();
    expect(wrapper.find('input[type="numericrange"]').exists()).toBe(true);
    expect(wrapper.find('input[type="datetimerange"]').exists()).toBe(true);
    expect(wrapper.find('.apqa-input-search-select-trigger').exists()).toBe(true);
    expect(wrapper.find('.apqa-input-multipunch-trigger').exists()).toBe(true);
  });

  it('renders the reusable regex text component', () => {
    const wrapper = mountGallery();
    expect(wrapper.find('.apqa-input-regex-text-input').exists()).toBe(true);
    expect(wrapper.find('.apqa-input-regex-text-toggle').text()).toBe('.*');
  });

  it('renders checkboxes, radios and a file picker', () => {
    const wrapper = mountGallery();
    expect(wrapper.find('input[type="checkbox"]').exists()).toBe(true);
    expect(wrapper.find('input[type="radio"]').exists()).toBe(true);
    expect(wrapper.find('input[type="file"]').exists()).toBe(true);
  });
});

import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import InputArgLiteralValue from './index.js';

function mountLiteral(value) {
  return mount(InputArgLiteralValue, {
    props: { value, name: 'value' },
  });
}

const typeSelect = (wrapper) => wrapper.find('select.apqa-input-literal-value-type');
const valueControl = (wrapper) => wrapper.find('.apqa-input-literal-value-editor');

describe('InputArgLiteralValue', () => {
  it('lists every literal type in the selector', () => {
    const wrapper = mountLiteral(null);
    const options = typeSelect(wrapper).findAll('option').map((o) => o.element.value);
    expect(options).toEqual(['text', 'number', 'boolean', 'path', 'date', 'json']);
  });

  it('detects a boolean value and renders a true/false select', () => {
    const wrapper = mountLiteral(true);
    expect(typeSelect(wrapper).element.value).toBe('boolean');
    expect(valueControl(wrapper).find('select').element.value).toBe('true');
  });

  it('detects a number value', () => {
    const wrapper = mountLiteral(42);
    expect(typeSelect(wrapper).element.value).toBe('number');
    expect(valueControl(wrapper).find('input[type="number"]').element.value).toBe('42');
  });

  it('detects a text value', () => {
    const wrapper = mountLiteral('abc');
    expect(typeSelect(wrapper).element.value).toBe('text');
    expect(valueControl(wrapper).find('input[type="text"]').element.value).toBe('abc');
  });

  it('detects an array value as json', () => {
    const wrapper = mountLiteral([1, 2]);
    expect(typeSelect(wrapper).element.value).toBe('json');
    expect(valueControl(wrapper).find('input[type="text"]').element.value).toBe('[1,2]');
  });

  it('switching to boolean emits false (coerced from a non-boolean)', async () => {
    const wrapper = mountLiteral('abc');
    await typeSelect(wrapper).setValue('boolean');
    expect(wrapper.emitted('update:value').at(-1)).toEqual([false]);
    expect(typeSelect(wrapper).element.value).toBe('boolean');
  });

  it('switching from boolean to text emits the stringified value', async () => {
    const wrapper = mountLiteral(true);
    await typeSelect(wrapper).setValue('text');
    expect(wrapper.emitted('update:value').at(-1)).toEqual(['true']);
  });

  it('switching to path/date coerces to a string', async () => {
    const wrapper = mountLiteral(42);
    await typeSelect(wrapper).setValue('path');
    expect(wrapper.emitted('update:value').at(-1)).toEqual(['42']);
  });

  it('editing the value keeps the selected type', async () => {
    const wrapper = mountLiteral('');
    await valueControl(wrapper).find('input[type="text"]').setValue('hello');
    expect(wrapper.emitted('update:value').at(-1)).toEqual(['hello']);
    expect(typeSelect(wrapper).element.value).toBe('text');
  });
});

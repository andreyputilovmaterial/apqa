import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import InputComparisonOp from './index.js';

const OPS = [
  { name: 'eq', op_args: [{ name: 'unordered_arrays', type: 'boolean', default: false }] },
  { name: 'lt', op_args: [] },
];

function mountOp(props = {}) {
  return mount(InputComparisonOp, { props: { ops: OPS, ...props } });
}

describe('InputComparisonOp', () => {
  it('renders a placeholder drop down when empty', () => {
    const wrapper = mountOp();
    const select = wrapper.find('select.apqa-input-comparison-op-select');
    expect(select.exists()).toBe(true);
    expect(select.element.value).toBe('');
  });

  it('emits the chosen op as the model value', async () => {
    const wrapper = mountOp();
    await wrapper.find('select.apqa-input-comparison-op-select').setValue('lt');
    expect(wrapper.emitted('update:modelValue').at(-1)).toEqual([
      { op: 'lt', op_args: {} },
    ]);
  });

  it('renders op_args inputs once selected', () => {
    const wrapper = mountOp({ modelValue: { op: 'eq', op_args: {} } });
    expect(wrapper.find('input[name="unordered_arrays"]').exists()).toBe(true);
  });

  it('emits updated op_args when a boolean option changes', async () => {
    const wrapper = mountOp({ modelValue: { op: 'eq', op_args: {} } });
    await wrapper.find('input[name="unordered_arrays"]').setValue(true);
    expect(wrapper.emitted('update:modelValue').at(-1)).toEqual([
      { op: 'eq', op_args: { unordered_arrays: true } },
    ]);
  });
});

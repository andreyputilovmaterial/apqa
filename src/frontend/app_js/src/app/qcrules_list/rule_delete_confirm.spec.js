import { describe, it, expect, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import RuleDeleteConfirm from './rule_delete_confirm.js';

function mountConfirm(props = {}) {
  return mount(RuleDeleteConfirm, {
    props: {
      resolve: vi.fn(),
      reject: vi.fn(),
      record: { id: 'wave-69', name: 'Wave 69' },
      ...props,
    },
  });
}

describe('RuleDeleteConfirm', () => {
  it('shows the rule name in the confirmation text', () => {
    const wrapper = mountConfirm();
    expect(wrapper.text()).toContain('Wave 69');
    expect(wrapper.text()).toContain('Delete rule');
  });

  it('resolves true when Delete is clicked', async () => {
    const resolve = vi.fn();
    const wrapper = mountConfirm({ resolve });
    await wrapper.find('.apqa-rule-delete-confirm-button-danger').trigger('click');
    expect(resolve).toHaveBeenCalledWith(true);
  });

  it('rejects when Cancel is clicked', async () => {
    const reject = vi.fn();
    const wrapper = mountConfirm({ reject });
    const buttons = wrapper.findAll('.apqa-rule-delete-confirm-button');
    await buttons[0].trigger('click'); // Cancel is the first button
    expect(reject).toHaveBeenCalled();
  });
});

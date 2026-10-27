import { describe, it, expect, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import RuleForm, { makeSlug } from './rule_form.js';

// `input_cmdlet` references the chain component by its global name for the
// `cmdlet-chains` arg type (to avoid a circular import); register a stub so the
// form mounts without global registration.
const ChainStub = { template: '<div class="chain-stub" />' };

function mountForm(props = {}) {
  return mount(RuleForm, {
    props: { resolve: vi.fn(), reject: vi.fn(), cmdlets: [], ops: [], tagSuggestions: [], ...props },
    global: { components: { 'component-input-cmdlet-chain': ChainStub } },
  });
}

describe('makeSlug', () => {
  it('lowercases and joins words with hyphens', () => {
    expect(makeSlug('Wave 69 Counts')).toBe('wave-69-counts');
  });

  it('folds accented letters to ASCII', () => {
    expect(makeSlug("Étude sur l'été")).toBe('etude-sur-l-ete');
  });

  it('prefixes a leading digit', () => {
    expect(makeSlug('2 Fast')).toBe('rule-2-fast');
  });

  it('falls back to "rule" when nothing is usable', () => {
    expect(makeSlug('!!!')).toBe('rule');
  });
});

describe('RuleForm', () => {
  it('auto-fills the technical id and resolves the payload on submit', async () => {
    const resolve = vi.fn();
    const wrapper = mountForm({ resolve });

    await wrapper.find('input[name="name"]').setValue('Wave 69');
    await wrapper.find('form').trigger('submit');

    expect(resolve).toHaveBeenCalledTimes(1);
    const payload = resolve.mock.calls[0][0];
    expect(payload.name).toBe('Wave 69');
    expect(payload.id).toBe('wave-69');
    expect(payload.group).toBe('');
    expect(payload.op).toBe('');
    expect(payload.left).toEqual([]);
    expect(payload.right).toEqual([]);
  });

  it('does not resolve when the name is empty', async () => {
    const resolve = vi.fn();
    const wrapper = mountForm({ resolve });

    await wrapper.find('form').trigger('submit');
    expect(resolve).not.toHaveBeenCalled();
  });
});

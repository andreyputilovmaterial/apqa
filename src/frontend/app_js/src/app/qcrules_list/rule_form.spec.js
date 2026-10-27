import { describe, it, expect, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import RuleForm, { ensureUnique, makeSlug, makeUniqueSlug } from './rule_form.js';

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

describe('makeUniqueSlug / ensureUnique', () => {
  it('keeps the slug when it is not already used', () => {
    expect(makeUniqueSlug('Wave 69', [])).toBe('wave-69');
  });

  it('appends -2 when the slug is already used', () => {
    expect(makeUniqueSlug('Wave 69', ['wave-69'])).toBe('wave-69-2');
  });

  it('keeps incrementing until a free id is found', () => {
    expect(makeUniqueSlug('Wave 69', ['wave-69', 'wave-69-2'])).toBe('wave-69-3');
  });

  it('preserves an already-valid slug and only deduplicates', () => {
    expect(ensureUnique('MyRule', [])).toBe('MyRule');
    expect(ensureUnique('MyRule', ['MyRule'])).toBe('MyRule-2');
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

  it('deduplicates the auto-filled id against existing ids', async () => {
    const resolve = vi.fn();
    const wrapper = mountForm({ resolve, existingIds: ['wave-69'] });

    await wrapper.find('input[name="name"]').setValue('Wave 69');
    await wrapper.find('form').trigger('submit');

    expect(resolve).toHaveBeenCalledTimes(1);
    expect(resolve.mock.calls[0][0].id).toBe('wave-69-2');
  });

  it('rejects a manually-entered id that already exists', async () => {
    const resolve = vi.fn();
    const wrapper = mountForm({ resolve, existingIds: ['taken'] });

    await wrapper.find('input[name="name"]').setValue('Wave 69');
    await wrapper.find('input[name="id"]').setValue('taken');
    await wrapper.find('form').trigger('submit');

    expect(resolve).not.toHaveBeenCalled();
    expect(wrapper.find('.apqa-rule-form-error').text()).toContain('already used');
  });

  it('generates a unique id when the id field is cleared', async () => {
    const resolve = vi.fn();
    const wrapper = mountForm({ resolve, existingIds: ['wave-69'] });

    await wrapper.find('input[name="name"]').setValue('Wave 69');
    await wrapper.find('input[name="id"]').setValue('');
    await wrapper.find('form').trigger('submit');

    expect(resolve).toHaveBeenCalledTimes(1);
    expect(resolve.mock.calls[0][0].id).toBe('wave-69-2');
  });
});

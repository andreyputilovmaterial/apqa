import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import RuleRecord from './rule_record.js';
import { cmdletComponents } from '@/common_components/cmdlet_components/index.js';
import { inputCmdletComponents } from '@/common_components/input_types/cmdlets/index.js';

function makeRecord(overrides = {}) {
  return {
    id: 'Rule A',
    name: 'Rule A',
    comment: 'check the count',
    left: [{ cmdlet: 'get-content', args: { path: 'a.sav' } }],
    op: 'eq',
    op_args: {},
    right: [{ cmdlet: 'count' }],
    markers: [],
    tags: [],
    meta: {},
    created_at: '',
    _filterMeta: { cssClasses: [] },
    ...overrides,
  };
}

const GLOBAL_COMPONENTS = {
  ...cmdletComponents,
  ...inputCmdletComponents,
};
const mountRuleRecord = mount.bind(null, RuleRecord);
function mountRecord(options = {}) {
  return mountRuleRecord({
    ...options,
    global: { components: { ...GLOBAL_COMPONENTS, ...options.global?.components } },
  });
}

describe('RuleRecord', () => {
  it('renders the always-shown card with name, comment and definition', () => {
    const wrapper = mountRecord({ props: { record: makeRecord() } });

    expect(wrapper.find('.apqa-rule-card').exists()).toBe(true);
    expect(wrapper.find('.apqa-rule-card-name').text()).toBe('Rule A');
    expect(wrapper.find('.apqa-rule-card-comment').text()).toBe('check the count');
    expect(wrapper.find('.apqa-rule-card-definition').exists()).toBe(true);
  });

  it('shows the four icon action buttons', () => {
    const wrapper = mountRecord({ props: { record: makeRecord() } });

    expect(wrapper.find('.apqa-record-action-edit i.ri-edit-box-line').exists()).toBe(true);
    expect(wrapper.find('.apqa-record-action-run i.ri-play-large-line').exists()).toBe(true);
    expect(wrapper.find('.apqa-record-action-duplicate i.ri-file-copy-line').exists()).toBe(true);
    expect(wrapper.find('.apqa-record-action-delete i.ri-delete-bin-6-line').exists()).toBe(true);
  });

  it('forwards edit, run, duplicate and delete actions with the record', async () => {
    const wrapper = mountRecord({ props: { record: makeRecord() } });

    await wrapper.find('.apqa-record-action-edit').trigger('click');
    await wrapper.find('.apqa-record-action-run').trigger('click');
    await wrapper.find('.apqa-record-action-duplicate').trigger('click');
    await wrapper.find('.apqa-record-action-delete').trigger('click');

    expect(wrapper.emitted('edit')).toHaveLength(1);
    expect(wrapper.emitted('edit')[0][0]).toMatchObject({ name: 'Rule A' });
    expect(wrapper.emitted('run')).toHaveLength(1);
    expect(wrapper.emitted('run')[0][0]).toMatchObject({ name: 'Rule A' });
    expect(wrapper.emitted('duplicate')).toHaveLength(1);
    expect(wrapper.emitted('duplicate')[0][0]).toMatchObject({ name: 'Rule A' });
    expect(wrapper.emitted('delete')).toHaveLength(1);
    expect(wrapper.emitted('delete')[0][0]).toMatchObject({ name: 'Rule A' });
  });

  it('has no expand/collapse arrow or toggle for rules', async () => {
    const wrapper = mountRecord({ props: { record: makeRecord() } });

    expect(wrapper.find('.apqa-rule-card .ri-arrow-down-double-fill').exists()).toBe(false);
    expect(wrapper.find('.apqa-rule-card .ri-arrow-up-double-fill').exists()).toBe(false);

    await wrapper.find('.apqa-rule-card-head').trigger('click');
    expect(wrapper.find('.apqa-rule-card').exists()).toBe(true);
    expect(wrapper.emitted('toggle')).toBeUndefined();
  });

  it('adds the shared base, rule kind and mark classes to the <li>', () => {
    const wrapper = mountRecord({
      props: { record: makeRecord({ markers: ['skip'], op: '', right: [] }) },
    });

    const li = wrapper.find('li');
    expect(li.classes()).toContain('apqa-rules-tree-item');
    expect(li.classes()).toContain('apqa-rule-record');
    expect(li.classes()).toContain('skip');
    expect(li.classes()).toContain('unfinished');
  });

  it('adds the invalid class when a rule references an unrecognized cmdlet', () => {
    const wrapper = mountRecord({
      props: {
        record: makeRecord({ left: [{ cmdlet: 'no-such-cmdlet', args: {} }] }),
        cmdlets: [{ name: 'count', kind: 'processor', args: [] }],
      },
    });

    expect(wrapper.find('li').classes()).toContain('invalid');
  });

  it('adds the invalid class when a rule references an unrecognized comparison op', () => {
    const wrapper = mountRecord({
      props: {
        record: makeRecord({ op: 'eq-unorderedd' }),
        ops: [{ name: 'eq' }],
      },
    });

    expect(wrapper.find('li').classes()).toContain('invalid');
  });

  it('keeps filter CSS classes from the record', () => {
    const wrapper = mountRecord({
      props: { record: makeRecord({ _filterMeta: { cssClasses: ['apqa-u-hidden'] } }) },
    });

    expect(wrapper.find('li').classes()).toContain('apqa-u-hidden');
  });

  it('renders the inline edit form when it is the rule being edited', () => {
    const wrapper = mountRecord({
      props: { record: makeRecord(), editingId: 'Rule A' },
    });

    expect(wrapper.find('.apqa-rule-edit-form').exists()).toBe(true);
    expect(wrapper.find('.apqa-record-action-save i.ri-save-3-line').exists()).toBe(true);
    expect(wrapper.find('.apqa-record-action-cancel i.ri-close-circle-line').exists()).toBe(true);
    expect(wrapper.find('.apqa-record-action-edit').exists()).toBe(false);
  });

  it('shows a green "Passed" banner for a cached passed result', () => {
    const wrapper = mountRecord({
      props: {
        record: makeRecord(),
        runResults: { 'Rule A': { status: 'passed', notes: [] } },
      },
    });

    const banner = wrapper.find('.apqa-rule-run-result-passed');
    expect(banner.exists()).toBe(true);
    expect(banner.text()).toBe('Passed');
  });

  it('shows a red "Failed" banner with notes for a cached failed result', () => {
    const wrapper = mountRecord({
      props: {
        record: makeRecord(),
        runResults: {
          'Rule A': {
            status: 'failed',
            notes: [{ path: ['Fields', 'A', 'Label'], message: 'not XML-compatible' }],
          },
        },
      },
    });

    expect(wrapper.find('.apqa-rule-run-result-failed').text()).toBe('Failed');
    expect(wrapper.find('.apqa-rule-run-result-notes li').text()).toContain(
      'Fields.A.Label: not XML-compatible',
    );
  });

  it('shows a red exception snippet for a cached error result', () => {
    const wrapper = mountRecord({
      props: {
        record: makeRecord(),
        runResults: {
          'Rule A': {
            status: 'error',
            message: "cmdlet 'nope' (step 0): cmdlet not found: nope",
          },
        },
      },
    });

    const error = wrapper.find('.apqa-rule-run-result-error');
    expect(error.exists()).toBe(true);
    expect(error.text()).toBe("cmdlet 'nope' (step 0): cmdlet not found: nope");
  });

  it('emits view-error with the traceback when the error has one', async () => {
    const wrapper = mountRecord({
      props: {
        record: makeRecord(),
        runResults: {
          'Rule A': {
            status: 'error',
            message: 'boom',
            traceback: 'Traceback (most recent call last):\n  boom',
          },
        },
      },
    });

    const button = wrapper.find('.apqa-rule-run-result-error-trace');
    expect(button.exists()).toBe(true);

    await button.trigger('click');

    expect(wrapper.emitted('view-error')).toHaveLength(1);
    expect(wrapper.emitted('view-error')[0][0]).toContain('Traceback');
  });

  it('shows no run-result banner when there is no cached result', () => {
    const wrapper = mountRecord({ props: { record: makeRecord() } });

    expect(wrapper.find('.apqa-rule-run-result').exists()).toBe(false);
  });

  it('shows a light grey empty tick when there is no cached result', () => {
    const wrapper = mountRecord({ props: { record: makeRecord() } });

    const tick = wrapper.find('.apqa-rule-run-tick');
    expect(tick.exists()).toBe(true);
    expect(tick.classes()).toContain('is-empty');
    expect(tick.find('i').exists()).toBe(false);
  });

  it('shows a green tick for a cached passed result', () => {
    const wrapper = mountRecord({
      props: {
        record: makeRecord(),
        runResults: { 'Rule A': { status: 'passed', notes: [] } },
      },
    });

    const tick = wrapper.find('.apqa-rule-run-tick');
    expect(tick.classes()).toContain('is-passed');
    expect(tick.find('i.ri-check-line').exists()).toBe(true);
    expect(tick.find('i.ri-close-fill').exists()).toBe(false);
  });

  it('shows a red cross for a cached failed result', () => {
    const wrapper = mountRecord({
      props: {
        record: makeRecord(),
        runResults: { 'Rule A': { status: 'failed', notes: [] } },
      },
    });

    const tick = wrapper.find('.apqa-rule-run-tick');
    expect(tick.classes()).toContain('is-failed');
    expect(tick.find('i.ri-close-fill').exists()).toBe(true);
  });

  it('shows a spinning loader for a cached running result', () => {
    const wrapper = mountRecord({
      props: {
        record: makeRecord(),
        runResults: { 'Rule A': { status: 'running' } },
      },
    });

    const tick = wrapper.find('.apqa-rule-run-tick');
    expect(tick.classes()).toContain('is-running');
    expect(tick.find('i.ri-loader-4-line').exists()).toBe(true);
  });

  it('shows a red cross for a cached errored result', () => {
    const wrapper = mountRecord({
      props: {
        record: makeRecord(),
        runResults: { 'Rule A': { status: 'error', message: 'boom' } },
      },
    });

    const tick = wrapper.find('.apqa-rule-run-tick');
    expect(tick.classes()).toContain('is-failed');
    expect(tick.find('i.ri-close-fill').exists()).toBe(true);
  });

  it('forwards save and cancel from the inline edit form', async () => {
    const wrapper = mountRecord({
      props: { record: makeRecord(), editingId: 'Rule A' },
    });

    await wrapper.find('input[name="name"]').setValue('Renamed');
    await wrapper.find('form').trigger('submit');

    expect(wrapper.emitted('save')).toHaveLength(1);
    expect(wrapper.emitted('save')[0][0]).toMatchObject({ name: 'Rule A' });
    expect(wrapper.emitted('save')[0][1]).toMatchObject({ name: 'Renamed' });

    await wrapper.find('.apqa-rule-form-button').trigger('click');
    expect(wrapper.emitted('cancel')).toHaveLength(1);
  });
});

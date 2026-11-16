import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import RuleBody from './rule_body.js';
import { INVALID_MESSAGE, UNFINISHED_MESSAGE } from './marks_badges.js';
import { cmdletComponents } from '@/common_components/cmdlet_components/index.js';

function makeRecord(overrides = {}) {
  return {
    id: 'Rule A',
    name: 'Rule A',
    comment: '',
    left: [{ cmdlet: 'get-content', args: { path: 'a.sav' } }],
    op: 'eq',
    op_args: {},
    right: [{ cmdlet: 'count' }],
    markers: [],
    tags: [],
    meta: {},
    created_at: '',
    ...overrides,
  };
}

const GLOBAL = { components: cmdletComponents };
const OPS = [{ name: 'eq', compact: [{ text: '=', role: 'symbol' }] }];

function mountBody(props = {}) {
  return mount(RuleBody, { global: GLOBAL, props });
}

describe('RuleBody', () => {
  it('renders the name and both sides of the rule', () => {
    const wrapper = mountBody({ record: makeRecord(), ops: OPS });
    const text = wrapper.text();

    expect(text).toContain('Rule A');
    expect(text).toContain('get-content path=a.sav');
    expect(text).toContain('=');
    expect(text).toContain('count');
  });

  it('renders a cmdlet compact display spec from its metadata', () => {
    const record = makeRecord({
      left: [{ cmdlet: 'get-content-excel', args: { path: '/data/map.xlsx' } }],
      right: [{ cmdlet: 'count' }],
    });
    const cmdlets = [
      {
        name: 'get-content-excel',
        kind: 'source',
        args: [{ name: 'path', type: 'path', required: true }],
        compact: [{ text: '[xlsx]', role: 'logo' }, { arg: 'path' }],
      },
    ];
    const wrapper = mountBody({ record, cmdlets, ops: OPS });
    const text = wrapper.text();

    expect(text).toContain('[xlsx]');
    expect(text).toContain('/data/map.xlsx');
    expect(text).not.toContain('get-content-excel');
  });

  it('renders a logical short form with nested operand chains', () => {
    const record = makeRecord({
      left: [
        {
          cmdlet: 'logical-and',
          args: {
            operands: [
              [{ cmdlet: 'get-content', args: { path: 'a.sav' } }],
              [{ cmdlet: 'get-content', args: { path: 'b.sav' } }],
            ],
          },
        },
      ],
      right: [{ cmdlet: 'count' }],
    });
    const cmdlets = [
      {
        name: 'logical-and',
        kind: 'source',
        args: [{ name: 'operands', type: 'cmdlet-chains', required: true }],
        compact: [
          { text: 'AND(' },
          { arg: 'operands', role: 'operands' },
          { text: ')' },
        ],
      },
      { name: 'get-content', kind: 'source', args: [{ name: 'path', type: 'path' }] },
    ];
    const wrapper = mountBody({ record, cmdlets, ops: OPS });
    const text = wrapper.text();

    expect(text).toContain('AND(');
    expect(text).toContain('get-content path=a.sav');
    expect(text).toContain(', ');
    expect(text).toContain('get-content path=b.sav');
    expect(text).toContain(')');
  });

  it('renders the comment only when present', () => {
    const withComment = mountBody({ record: makeRecord({ comment: 'check the count' }), ops: OPS });
    expect(withComment.text()).toContain('check the count');

    const withoutComment = mountBody({ record: makeRecord(), ops: OPS });
    expect(withoutComment.text()).not.toContain('check the count');
  });

  it('renders tags in the meta row', () => {
    const wrapper = mountBody({
      record: makeRecord({ tags: ['counts', 'wave69'] }),
      ops: OPS,
    });

    expect(wrapper.find('.apqa-record-tags').text()).toBe('counts, wave69');
  });

  it('does not render a meta row for an unmarked, untagged rule', () => {
    const wrapper = mountBody({ record: makeRecord(), ops: OPS });
    expect(wrapper.find('.apqa-record-meta').exists()).toBe(false);
  });

  it('shows an unfinished helper note under the name', () => {
    const wrapper = mountBody({ record: makeRecord({ op: '', right: [] }), ops: OPS });

    expect(wrapper.find('.apqa-rule-unfinished-note').text()).toBe(UNFINISHED_MESSAGE);
  });

  it('shows an invalid helper note under the name for an unrecognized cmdlet', () => {
    const record = makeRecord({ left: [{ cmdlet: 'no-such-cmdlet', args: {} }] });
    const cmdlets = [{ name: 'count', kind: 'processor', args: [] }];
    const wrapper = mountBody({ record, cmdlets, ops: OPS });

    expect(wrapper.find('.apqa-rule-invalid-note').text()).toBe(INVALID_MESSAGE);
  });
});

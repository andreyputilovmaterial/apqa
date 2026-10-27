import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';

import MarksBadges, { UNFINISHED_MESSAGE } from './marks_badges.js';

describe('MarksBadges', () => {
  it('renders nothing when there are no marks', () => {
    const wrapper = mount(MarksBadges, { props: { marks: [] } });
    expect(wrapper.find('.apqa-marks-badges').exists()).toBe(false);
  });

  it('renders a plain badge per mark', () => {
    const wrapper = mount(MarksBadges, { props: { marks: ['skip', 'xfail'] } });

    const badges = wrapper.findAll('.apqa-mark-badge');
    expect(badges.map((badge) => badge.text())).toEqual(['skip', 'xfail']);
    expect(badges[0].attributes('title')).toBeUndefined();
    expect(badges[1].attributes('title')).toBeUndefined();
  });

  it('adds a title tooltip to the unfinished badge', () => {
    const wrapper = mount(MarksBadges, { props: { marks: ['unfinished'] } });

    expect(wrapper.find('.apqa-mark-badge').attributes('title')).toBe(UNFINISHED_MESSAGE);
  });

  it('adds a per-mark class modifier', () => {
    const wrapper = mount(MarksBadges, { props: { marks: ['skip'] } });

    expect(wrapper.find('.apqa-mark-badge-skip').exists()).toBe(true);
  });
});

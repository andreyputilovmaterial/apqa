import { describe, it, expect } from 'vitest';

import { formatPath, formatNote, groupRunSummary } from './run_result.js';

describe('formatPath', () => {
  it('joins identifier keys with dots', () => {
    expect(formatPath(['Fields', 'A', 'Label'])).toBe('Fields.A.Label');
  });

  it('renders array indices as [i]', () => {
    expect(formatPath(['Pages', 'Q1', 'value', 2])).toBe('Pages.Q1.value[2]');
  });

  it('quotes non-identifier keys', () => {
    expect(formatPath(['Pages', 'Q1', 'Categories', 'None of the above', 'Label'])).toBe(
      "Pages.Q1.Categories['None of the above'].Label",
    );
  });

  it('returns an empty string for an empty path', () => {
    expect(formatPath([])).toBe('');
    expect(formatPath(undefined)).toBe('');
  });
});

describe('formatNote', () => {
  it('renders path: message', () => {
    expect(formatNote({ path: ['Fields', 'A', 'Label'], message: 'bad' })).toBe(
      'Fields.A.Label: bad',
    );
  });

  it('renders just the message when the path is empty', () => {
    expect(formatNote({ path: [], message: 'bad' })).toBe('bad');
  });

  it('handles a missing message', () => {
    expect(formatNote({ path: ['a'] })).toBe('a: ');
  });
});

describe('groupRunSummary', () => {
  it('renders passed and failed counts like pytest', () => {
    expect(
      groupRunSummary({ total: 5, passed: 3, failed: 1, errored: 0, running: 0, blank: 1 }),
    ).toBe('3 passed, 1 failed, 1 queued');
  });

  it('omits zero counts', () => {
    expect(
      groupRunSummary({ total: 2, passed: 2, failed: 0, errored: 0, running: 0, blank: 0 }),
    ).toBe('2 passed');
  });

  it('distinguishes error from failed', () => {
    expect(
      groupRunSummary({ total: 2, passed: 0, failed: 1, errored: 1, running: 0, blank: 0 }),
    ).toBe('1 failed, 1 error');
  });

  it('shows running and queued counts', () => {
    expect(
      groupRunSummary({ total: 4, passed: 1, failed: 0, errored: 0, running: 1, blank: 2 }),
    ).toBe('1 passed, 1 running, 2 queued');
  });

  it('returns an empty string when there are no rules', () => {
    expect(groupRunSummary(null)).toBe('');
    expect(
      groupRunSummary({ total: 0, passed: 0, failed: 0, errored: 0, running: 0, blank: 0 }),
    ).toBe('');
  });
});

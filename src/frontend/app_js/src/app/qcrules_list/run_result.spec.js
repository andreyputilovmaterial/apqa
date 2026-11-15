import { describe, it, expect } from 'vitest';

import { formatPath, formatNote } from './run_result.js';

describe('formatPath', () => {
  it('joins identifier keys with dots', () => {
    expect(formatPath(['fields', 'A', 'label'])).toBe('fields.A.label');
  });

  it('renders array indices as [i]', () => {
    expect(formatPath(['pages', 'Q1', 'value', 2])).toBe('pages.Q1.value[2]');
  });

  it('quotes non-identifier keys', () => {
    expect(formatPath(['pages', 'Q1', 'categories', 'None of the above', 'label'])).toBe(
      "pages.Q1.categories['None of the above'].label",
    );
  });

  it('returns an empty string for an empty path', () => {
    expect(formatPath([])).toBe('');
    expect(formatPath(undefined)).toBe('');
  });
});

describe('formatNote', () => {
  it('renders path: message', () => {
    expect(formatNote({ path: ['fields', 'A', 'label'], message: 'bad' })).toBe(
      'fields.A.label: bad',
    );
  });

  it('renders just the message when the path is empty', () => {
    expect(formatNote({ path: [], message: 'bad' })).toBe('bad');
  });

  it('handles a missing message', () => {
    expect(formatNote({ path: ['a'] })).toBe('a: ');
  });
});

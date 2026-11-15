import { describe, it, expect } from 'vitest';
import { formatLiteralValue } from './shared.js';

describe('formatLiteralValue', () => {
  it('quotes text so it stays distinct from booleans/numbers', () => {
    expect(formatLiteralValue('true')).toBe('"true"');
    expect(formatLiteralValue('hello')).toBe('"hello"');
    expect(formatLiteralValue('')).toBe('""');
  });

  it('renders booleans and numbers bare', () => {
    expect(formatLiteralValue(true)).toBe('true');
    expect(formatLiteralValue(false)).toBe('false');
    expect(formatLiteralValue(42)).toBe('42');
  });

  it('renders null and undefined', () => {
    expect(formatLiteralValue(null)).toBe('null');
    expect(formatLiteralValue(undefined)).toBe('');
  });

  it('renders arrays and objects as JSON', () => {
    expect(formatLiteralValue([1, 2])).toBe('[1,2]');
    expect(formatLiteralValue({ a: 1 })).toBe('{"a":1}');
  });
});

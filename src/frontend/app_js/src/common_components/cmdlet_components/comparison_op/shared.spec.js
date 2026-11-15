import { describe, it, expect } from 'vitest';
import { comparisonSymbol } from './shared.js';

describe('comparisonSymbol', () => {
  it('maps known ops to symbols', () => {
    expect(comparisonSymbol('eq')).toBe('=');
    expect(comparisonSymbol('lt')).toBe('<');
    expect(comparisonSymbol('gt')).toBe('>');
  });

  it('falls back to the raw op name', () => {
    expect(comparisonSymbol('contains')).toBe('contains');
  });

  it('falls back to a placeholder for an empty op', () => {
    expect(comparisonSymbol('')).toBe('?');
    expect(comparisonSymbol(undefined)).toBe('?');
  });
});

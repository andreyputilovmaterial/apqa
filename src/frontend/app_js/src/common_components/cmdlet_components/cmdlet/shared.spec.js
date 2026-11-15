import { describe, it, expect } from 'vitest';
import { formatArgValue, partClasses, argType } from './shared.js';

describe('formatArgValue', () => {
  it('renders scalars as text and undefined as empty', () => {
    expect(formatArgValue('Title Details')).toBe('Title Details');
    expect(formatArgValue(9002)).toBe('9002');
    expect(formatArgValue(true)).toBe('true');
    expect(formatArgValue(undefined)).toBe('');
  });

  it('serializes objects to JSON', () => {
    expect(formatArgValue({ a: 1 })).toBe('{"a":1}');
    expect(formatArgValue([1, 2])).toBe('[1,2]');
  });
});

describe('partClasses', () => {
  it('gives literal text parts the text kind class', () => {
    expect(partClasses({ text: '[xlsx]' })).toBe('apqa-cmdlet-part apqa-cmdlet-part-text');
  });

  it('gives arg parts the arg kind class', () => {
    expect(partClasses({ arg: 'path' })).toBe('apqa-cmdlet-part apqa-cmdlet-part-arg');
  });

  it('adds a role class when the part carries a role', () => {
    expect(partClasses({ text: '[xlsx]', role: 'logo' })).toBe(
      'apqa-cmdlet-part apqa-cmdlet-part-text apqa-cmdlet-role-logo',
    );
  });

  it('falls back to the base class for a missing part', () => {
    expect(partClasses(null)).toBe('apqa-cmdlet-part');
  });
});

describe('argType', () => {
  it('returns the declared type for a known arg', () => {
    const meta = { args: [{ name: 'path', type: 'path' }] };
    expect(argType(meta, 'path')).toBe('path');
  });

  it('falls back to text for unknown args or missing metadata', () => {
    expect(argType({ args: [] }, 'path')).toBe('text');
    expect(argType(null, 'path')).toBe('text');
  });
});

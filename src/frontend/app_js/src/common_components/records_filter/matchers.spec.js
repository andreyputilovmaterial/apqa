import { describe, it, expect } from 'vitest'
import {
  matchText,
  matchNumericRange,
  matchDatetimeRange,
  matchValue,
  compareValues,
  matchesRecord,
} from './matchers.js'

describe('matchText', () => {
  it('matches anything when the filter is blank', () => {
    expect(matchText('Alps', '')).toBe(true)
    expect(matchText('Alps', '   ')).toBe(true)
    expect(matchText('Alps', null)).toBe(true)
  })

  it('matches by case-insensitive substring', () => {
    expect(matchText('Alps hiking 2025', 'alps')).toBe(true)
    expect(matchText('Alps hiking 2025', 'HIKING')).toBe(true)
    expect(matchText('Alps hiking 2025', 'ps hik')).toBe(true)
  })

  it('returns false when the text does not match', () => {
    expect(matchText('Alps', 'japan')).toBe(false)
  })

  it('matches arrays by joining their items', () => {
    expect(matchText(['hiking', 'friends', 'mountains'], 'friend')).toBe(true)
    expect(matchText(['hiking', 'friends'], 'japan')).toBe(false)
  })

  it('handles empty field values', () => {
    expect(matchText('', 'x')).toBe(false)
    expect(matchText(null, 'x')).toBe(false)
  })
})

describe('matchNumericRange', () => {
  it('matches anything for a blank range', () => {
    expect(matchNumericRange(10, null)).toBe(true)
    expect(matchNumericRange(10, {})).toBe(true)
  })

  it('matches with only a start', () => {
    expect(matchNumericRange(10, { from: 5 })).toBe(true)
    expect(matchNumericRange(3, { from: 5 })).toBe(false)
  })

  it('matches with only an end', () => {
    expect(matchNumericRange(10, { to: 20 })).toBe(true)
    expect(matchNumericRange(30, { to: 20 })).toBe(false)
  })

  it('matches within a start..end range', () => {
    expect(matchNumericRange(10, { from: 5, to: 20 })).toBe(true)
    expect(matchNumericRange(2, { from: 5, to: 20 })).toBe(false)
    expect(matchNumericRange(50, { from: 5, to: 20 })).toBe(false)
  })
})

describe('matchDatetimeRange', () => {
  it('matches anything for a blank range', () => {
    expect(matchDatetimeRange('2025-07-15T10:00:00Z', null)).toBe(true)
    expect(matchDatetimeRange('2025-07-15T10:00:00Z', {})).toBe(true)
  })

  it('matches with only a start date', () => {
    expect(matchDatetimeRange('2025-07-15T10:00:00Z', { from: '2025-01-01' })).toBe(true)
    expect(matchDatetimeRange('2024-01-01T00:00:00Z', { from: '2025-01-01' })).toBe(false)
  })

  it('matches with only an end date', () => {
    expect(matchDatetimeRange('2024-06-01T00:00:00Z', { to: '2024-12-31' })).toBe(true)
    expect(matchDatetimeRange('2025-06-01T00:00:00Z', { to: '2024-12-31' })).toBe(false)
  })

  it('matches within a start..end range', () => {
    expect(matchDatetimeRange('2024-06-01T00:00:00Z', { from: '2024-01-01', to: '2024-12-31' })).toBe(true)
    expect(matchDatetimeRange('2023-01-01T00:00:00Z', { from: '2024-01-01', to: '2024-12-31' })).toBe(false)
    expect(matchDatetimeRange('2025-01-01T00:00:00Z', { from: '2024-01-01', to: '2024-12-31' })).toBe(false)
  })
})

describe('matchValue', () => {
  it('dispatches to the right matcher by type', () => {
    expect(matchValue('Alps', 'alps', 'text')).toBe(true)
    expect(matchValue(10, { from: 5 }, 'number')).toBe(true)
    expect(matchValue('2024-06-01', { from: '2024-01-01' }, 'date')).toBe(true)
    expect(matchValue('2024-06-01T00:00:00Z', { from: '2024-01-01' }, 'datetime')).toBe(true)
  })
})

describe('compareValues', () => {
  it('sorts text both ways', () => {
    expect(compareValues('Alps', 'Japan', 'text', true)).toBeLessThan(0)
    expect(compareValues('Alps', 'Japan', 'text', false)).toBeGreaterThan(0)
  })

  it('sorts numbers both ways', () => {
    expect(compareValues(5, 10, 'number', true)).toBeLessThan(0)
    expect(compareValues(5, 10, 'number', false)).toBeGreaterThan(0)
  })

  it('sorts dates chronologically both ways', () => {
    expect(compareValues('2024-01-01', '2025-01-01', 'date', true)).toBeLessThan(0)
    expect(compareValues('2024-01-01', '2025-01-01', 'date', false)).toBeGreaterThan(0)
  })
})

describe('matchesRecord (filter combinations)', () => {
  const record = {
    name: 'Alps hiking 2025',
    place: 'Switzerland',
    tags: ['hiking', 'friends'],
    year: 2025,
    eventDate: '2025-07-12',
  }

  const columns = {
    name: { type: 'text' },
    place: { type: 'text' },
    tags: { type: 'text' },
    year: { type: 'number' },
    eventDate: { type: 'date' },
  }

  const blank = { name: '', place: '', tags: '', year: '', eventDate: '' }

  it('matches when every filter is blank', () => {
    expect(matchesRecord(record, blank, columns)).toBe(true)
  })

  it('matches when one box is filled and the rest are blank', () => {
    expect(matchesRecord(record, { ...blank, name: 'alps' }, columns)).toBe(true)
    expect(matchesRecord(record, { ...blank, place: 'swit' }, columns)).toBe(true)
    expect(matchesRecord(record, { ...blank, tags: 'friend' }, columns)).toBe(true)
    expect(matchesRecord(record, { ...blank, year: { from: 2020 } }, columns)).toBe(true)
    expect(matchesRecord(record, { ...blank, eventDate: { to: '2025-12-31' } }, columns)).toBe(true)
  })

  it('does not match when one box fails while others are blank', () => {
    expect(matchesRecord(record, { ...blank, name: 'japan' }, columns)).toBe(false)
    expect(matchesRecord(record, { ...blank, place: 'Japan' }, columns)).toBe(false)
    expect(matchesRecord(record, { ...blank, year: { to: 2000 } }, columns)).toBe(false)
    expect(matchesRecord(record, { ...blank, eventDate: { from: '2026-01-01' } }, columns)).toBe(false)
  })

  it('matches date ranges with empty start or end', () => {
    expect(matchesRecord(record, { ...blank, eventDate: { from: '2025-01-01', to: null } }, columns)).toBe(true)
    expect(matchesRecord(record, { ...blank, eventDate: { from: null, to: '2024-12-31' } }, columns)).toBe(false)
  })

  it('combines multiple filled boxes (all must match)', () => {
    expect(
      matchesRecord(record, { ...blank, name: 'alps', year: { from: 2025 }, eventDate: { from: '2025-01-01' } }, columns)
    ).toBe(true)

    expect(
      matchesRecord(record, { ...blank, name: 'alps', year: { from: 2026 } }, columns)
    ).toBe(false)
  })
})

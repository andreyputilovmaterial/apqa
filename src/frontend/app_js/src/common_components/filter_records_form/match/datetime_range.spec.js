import { describe, it, expect } from 'vitest'
import matchDatetimeRange from './datetime_range'

describe('matchDatetimeRange (filter_records_form)', () => {
  it('matches anything for a blank range', () => {
    expect(matchDatetimeRange(new Date('2025-07-15T10:00:00Z'), null)).toBe(true)
    expect(matchDatetimeRange(new Date('2025-07-15T10:00:00Z'), {})).toBe(true)
  })

  it('compares Date objects by timestamp', () => {
    const value = new Date('2024-06-01T00:00:00Z')
    expect(matchDatetimeRange(value, { from: new Date('2024-01-01T00:00:00Z') })).toBe(true)
    expect(matchDatetimeRange(value, { from: new Date('2024-07-01T00:00:00Z') })).toBe(false)
    expect(matchDatetimeRange(value, { to: new Date('2024-12-31T00:00:00Z') })).toBe(true)
    expect(matchDatetimeRange(value, { to: new Date('2024-05-31T00:00:00Z') })).toBe(false)
    expect(matchDatetimeRange(value, {
      from: new Date('2024-01-01T00:00:00Z'),
      to: new Date('2024-12-31T00:00:00Z'),
    })).toBe(true)
  })

  it('still accepts ISO string field values defensively', () => {
    expect(matchDatetimeRange('2024-06-01T00:00:00Z', { from: new Date('2024-01-01T00:00:00Z') })).toBe(true)
    expect(matchDatetimeRange('2023-01-01T00:00:00Z', { from: new Date('2024-01-01T00:00:00Z') })).toBe(false)
  })

  it('does not match an invalid field value when a range is set', () => {
    expect(matchDatetimeRange('not a date', { from: new Date('2024-01-01T00:00:00Z') })).toBe(false)
  })
})

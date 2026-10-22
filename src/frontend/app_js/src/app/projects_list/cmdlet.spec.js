import { describe, it, expect } from 'vitest'
import { cmdletText } from './cmdlet.js'
import { comparisonSymbol } from './comparison.js'

describe('cmdletText', () => {
  it('renders the default "name args" form', () => {
    expect(cmdletText({ cmdlet: 'get-content', args: { path: '/data/a.sav' } })).toBe('get-content path=/data/a.sav')
    expect(cmdletText({ cmdlet: 'count' })).toBe('count')
  })

  it('renders boolean args as flags', () => {
    expect(cmdletText({ cmdlet: 'get-childitem', args: { recurse: true } })).toBe('get-childitem recurse')
  })

  it('renders the literal cmdlet as its value only', () => {
    expect(cmdletText({ cmdlet: 'literal', args: { value: 9002 } })).toBe('9002')
    expect(cmdletText({ cmdlet: 'literal', args: { value: 'Title Details' } })).toBe('Title Details')
  })
})

describe('comparisonSymbol', () => {
  it('maps known ops to symbols', () => {
    expect(comparisonSymbol('eq')).toBe('=')
    expect(comparisonSymbol('lt')).toBe('<')
    expect(comparisonSymbol('gt')).toBe('>')
  })

  it('falls back to the raw op name', () => {
    expect(comparisonSymbol('contains')).toBe('contains')
  })

  it('falls back to a placeholder for an empty op', () => {
    expect(comparisonSymbol('')).toBe('?')
    expect(comparisonSymbol(undefined)).toBe('?')
  })
})

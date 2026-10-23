import { describe, it, expect } from 'vitest'
import { cmdletParts, cmdletText } from './cmdlet.js'
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

describe('cmdletParts', () => {
  it('splits the default form into the name and each argument', () => {
    expect(cmdletParts({ cmdlet: 'get-content', args: { path: '/data/a.sav' } })).toEqual([
      'get-content',
      'path=/data/a.sav',
    ])
    expect(cmdletParts({ cmdlet: 'count' })).toEqual(['count'])
  })

  it('keeps boolean args as bare flags', () => {
    expect(cmdletParts({ cmdlet: 'get-childitem', args: { recurse: true } })).toEqual([
      'get-childitem',
      'recurse',
    ])
  })

  it('treats a custom renderer output as a single part', () => {
    expect(cmdletParts({ cmdlet: 'literal', args: { value: 'Title Details' } })).toEqual(['Title Details'])
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

// Pure, isolated matching/sorting helpers used by RecordsFilter.
// Kept dependency-free so they can be unit-tested on their own.

const toText = (value) => {
  if (value == null) return ''
  if (Array.isArray(value)) return value.map((item) => String(item)).join(' ')
  return String(value)
}

const isEmpty = (value) => {
  if (typeof value === 'number') return false
  return value == null || /^\s*$/.test(String(value))
}

export function matchText(fieldValue, matchValue) {
  if (isEmpty(matchValue)) return true
  return toText(fieldValue).toLowerCase().includes(String(matchValue).toLowerCase())
}

export function matchNumericRange(fieldValue, matchValue) {
  const { from, to } = matchValue || {}
  const num = Number(fieldValue)
  let ok = true
  if (!isEmpty(from)) ok = ok && Number.isFinite(num) && num >= Number(from)
  if (!isEmpty(to)) ok = ok && Number.isFinite(num) && num <= Number(to)
  return ok
}

export function matchDatetimeRange(fieldValue, matchValue) {
  const { from, to } = matchValue || {}
  const time = new Date(fieldValue).getTime()
  let ok = true
  if (!isEmpty(from)) ok = ok && Number.isFinite(time) && time >= new Date(from).getTime()
  if (!isEmpty(to)) ok = ok && Number.isFinite(time) && time <= new Date(to).getTime()
  return ok
}

export function matchValue(fieldValue, matchValue, type = 'text') {
  if (type === 'number') return matchNumericRange(fieldValue, matchValue)
  if (type === 'date' || type === 'datetime') return matchDatetimeRange(fieldValue, matchValue)
  return matchText(fieldValue, matchValue)
}

export function compareValues(a, b, type = 'text', ascending = true) {
  const dir = ascending ? 1 : -1
  if (type === 'number') {
    const na = Number.isFinite(Number(a)) ? Number(a) : 0
    const nb = Number.isFinite(Number(b)) ? Number(b) : 0
    return (na - nb) * dir
  }
  if (type === 'date' || type === 'datetime') {
    const ta = new Date(a).getTime()
    const tb = new Date(b).getTime()
    const na = Number.isFinite(ta) ? ta : 0
    const nb = Number.isFinite(tb) ? tb : 0
    return (na - nb) * dir
  }
  return toText(a).localeCompare(toText(b)) * dir
}

export function matchesRecord(record, filters, columns) {
  return Object.keys(columns).every((key) =>
    matchValue(record[key], filters[key], columns[key]?.type || 'text')
  )
}

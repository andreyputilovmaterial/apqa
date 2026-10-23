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

// ---- Compact filter summary -------------------------------------------------
// Used by RecordsFilter's collapsed one-line header. Kept here (rather than in
// the component) so it stays free of Vue and can be unit-tested alongside the
// matchers.

const pad2 = (n) => String(n).padStart(2, '0')

function formatDateEndpoint(value) {
  const date = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  return `${date.getFullYear()}-${pad2(date.getMonth() + 1)}-${pad2(date.getDate())}`
}

function formatDateTimeEndpoint(value) {
  const date = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  return `${formatDateEndpoint(date)} ${pad2(date.getHours())}:${pad2(date.getMinutes())}`
}

function formatRangeEndpoint(value, type) {
  if (type === 'number') return String(value)
  return type === 'datetime' ? formatDateTimeEndpoint(value) : formatDateEndpoint(value)
}

function summarizeRangeValue(value, type) {
  if (!value || typeof value !== 'object') return ''
  const hasFrom = !isEmpty(value.from)
  const hasTo = !isEmpty(value.to)
  if (!hasFrom && !hasTo) return ''
  const fromText = hasFrom ? formatRangeEndpoint(value.from, type) : ''
  const toText = hasTo ? formatRangeEndpoint(value.to, type) : ''
  if (hasFrom && hasTo) return `${fromText}..${toText}`
  if (hasFrom) return `≥ ${fromText}`
  return `≤ ${toText}`
}

function summarizeFilterValue(value, type) {
  if (type === 'number' || type === 'date' || type === 'datetime') {
    return summarizeRangeValue(value, type)
  }
  return value == null ? '' : String(value).trim()
}

// One "<label>: <value>" entry per non-empty filter, in column order. An empty
// array means "no filter applied".
export function summarizeFilters(filters, columns) {
  const parts = []
  for (const key of Object.keys(columns)) {
    const def = columns[key] || {}
    const type = def.type || 'text'
    const label = def.label || key
    const text = summarizeFilterValue(filters[key], type)
    if (text) parts.push(`${label}: ${text}`)
  }
  return parts
}

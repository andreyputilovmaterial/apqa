

function hasValue(value) {
  if( typeof value==='number' )
    return true;
  else if( typeof value==='string' )
    return !(/^\s*$/.test(value))
  else
    return !!value;
}

function toDate(value) {
  if (value == null || value === '') {
    return null;
  }
  const date = value instanceof Date ? value : new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}



function parseInput(input) {
  if( !input )
    return [ null, null ];
  const low = input?.from;
  const high = input?.to;
  return [ hasValue(low) ? toDate(low) : null, hasValue(high) ? toDate(high) : null ];
}

function match(fieldValue,matchValue) {
  const [low,high] = parseInput(matchValue);
  const value = toDate(fieldValue);
  let isGood = true;
  if( low )
    isGood = isGood && !!value && (value.getTime() >= low.getTime());
  if( high )
    isGood = isGood && !!value && (value.getTime() <= high.getTime());
  return isGood;
}

export default match;

import { computed } from 'vue';

// `literal-value` display: render the stored value so its type is visible at
// a glance. The stored form is a typed wrapper `{ type, value }` (or
// `{ type: 'sysmissing' }`); a bare JSON value (older rules) is rendered the
// same way. Text is quoted (so text "true" is distinguishable from boolean
// `true`), numbers/booleans render bare, `null` renders as `null`, and arrays /
// objects render as compact JSON.
export function formatLiteralValue(value) {
  if (value === undefined) return '';
  const raw = (
    value !== null && typeof value === 'object' && typeof value.type === 'string'
  )
    ? (value.type === 'sysmissing' ? null : value.value)
    : value;
  if (typeof raw === 'string') return JSON.stringify(raw);
  if (raw === null) return 'null';
  if (typeof raw === 'object') return JSON.stringify(raw);
  return String(raw);
}

export function makeLiteralValueRenderer() {
  return {
    props: { value: { default: undefined } },
    setup(props) {
      const text = computed(() => formatLiteralValue(props.value));
      return { text };
    },
    template: `{{ text }}`,
  };
}


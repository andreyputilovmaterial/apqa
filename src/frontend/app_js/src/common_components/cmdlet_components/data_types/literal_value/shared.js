import { computed } from 'vue';

// `literal-value` display: render the stored JSON value so its type is visible at
// a glance. Text is quoted (so text "true" is distinguishable from boolean
// `true`), numbers/booleans render bare, `null` renders as `null`, and arrays /
// objects render as compact JSON.
export function formatLiteralValue(value) {
  if (value === undefined) return '';
  if (typeof value === 'string') return JSON.stringify(value);
  if (value === null) return 'null';
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
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

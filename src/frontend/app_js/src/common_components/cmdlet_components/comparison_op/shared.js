import { computed } from 'vue';

import './styles.css';

// Comparison ops mapped to a display symbol. Ops without a mapping fall back to
// their raw name (e.g. `contains`).
const OP_SYMBOLS = {
  eq: '=',
  ne: '≠',
  lt: '<',
  le: '≤',
  gt: '>',
  ge: '≥',
};

export function comparisonSymbol(op) {
  return OP_SYMBOLS[op] ?? (op || '?');
}

// The comparison op chip. The full form is currently identical to the compact
// form (placeholder).
export const ComparisonOp = {
  props: { op: { type: String, default: '' } },
  template: `<span class="apqa-cmdlet apqa-comparison" :title="op || ''">{{ symbol }}</span>`,
  setup(props) {
    const symbol = computed(() => comparisonSymbol(props.op));
    return { symbol };
  },
};

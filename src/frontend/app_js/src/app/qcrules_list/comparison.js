import { computed } from 'vue';

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

const Comparison = {
  props: ['op'],
  template: `<span class="apqa-comparison" :title="op || ''">{{ symbol }}</span>`,
  setup(props) {
    const symbol = computed(() => comparisonSymbol(props.op));
    return { symbol };
  },
};

export default Comparison;

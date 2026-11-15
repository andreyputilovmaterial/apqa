import { computed } from 'vue';

import { partClasses } from '../cmdlet/shared';

import './styles.css';

// Pure helper: the display spec for an op in a given form, or null when the op
// (or that form's spec) is not declared — the component then falls back to the
// raw op name.
export function opSpec(ops, op, form) {
  const meta = (ops || []).find((o) => o.name === op);
  const value = meta && meta[form];
  return Array.isArray(value) ? value : null;
}

// The comparison op chip, rendered in a given `form` (`compact` or `full`). The
// symbol now comes from the op's metadata display spec — declared next to each
// `@comparisons.register(...)` in `src/cmdlets` — never from a hardcoded
// frontend map; an op without a spec falls back to its raw name.
export function makeComparisonOp(form) {
  return {
    props: {
      op: { type: String, default: '' },
      ops: { type: Array, default: () => [] },
    },

    setup(props) {
      const spec = computed(() => opSpec(props.ops, props.op, form));
      return { spec, partClasses };
    },

    template: `
<span class="apqa-cmdlet apqa-comparison" :title="op || ''">
  <template v-if="spec !== null">
    <span v-for="(part, index) in spec" :key="index" :class="partClasses(part)">{{ part.text }}</span>
  </template>
  <span v-else class="apqa-cmdlet-part">{{ op || '?' }}</span>
</span>
`,
  };
}

import { computed } from 'vue';

import { formatArgValue } from '../cmdlet/shared';

// Shared placeholder implementation for all per-type arg-value display
// components. Each data type has its own compact/full modules; for now they all
// render the same generic value text and will diverge per type later.
export function makeValueRenderer() {
  return {
    props: { value: { default: undefined } },
    setup(props) {
      const text = computed(() => formatArgValue(props.value));
      return { text };
    },
    template: `{{ text }}`,
  };
}

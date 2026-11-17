import { computed } from 'vue';

function label(rule) {
  if (!rule || typeof rule !== 'object') return '';
  const name = rule.name;
  const pattern = rule.pattern;
  if (name && pattern) return `${name}: ${pattern}`;
  return name || pattern || '';
}

// Read-only display of a `path-rules` arg value: the rules joined by a comma,
// each shown as "name: pattern" (or just whichever is present).
export default {
  props: { value: { default: () => [] } },
  setup(props) {
    const text = computed(() =>
      (Array.isArray(props.value) ? props.value : [])
        .map(label)
        .filter((s) => s !== '')
        .join(', '),
    );
    return { text };
  },
  template: `{{ text }}`,
};

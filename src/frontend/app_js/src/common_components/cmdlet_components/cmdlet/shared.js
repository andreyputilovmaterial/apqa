import { computed } from 'vue';

import './styles.css';

// Pure text form of one arg value (used by the per-type value renderers and by
// the display-spec arg parts).
export function formatArgValue(value) {
  if (value === undefined) return '';
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}

// CSS classes for one display-spec part. A part is either a literal token
// (`{ text, role? }`) or an arg reference (`{ arg, role? }`). The base
// `apqa-cmdlet-part` class is always present; `apqa-cmdlet-part-text` /
// `apqa-cmdlet-part-arg` mark the part kind, and `apqa-cmdlet-role-<role>` is
// added when the part carries a semantic role (logo, separator, symbol, …).
export function partClasses(part) {
  if (!part) return 'apqa-cmdlet-part';
  const classes = ['apqa-cmdlet-part'];
  if (Object.prototype.hasOwnProperty.call(part, 'arg')) {
    classes.push('apqa-cmdlet-part-arg');
  } else if (Object.prototype.hasOwnProperty.call(part, 'text')) {
    classes.push('apqa-cmdlet-part-text');
  }
  if (part.role) classes.push(`apqa-cmdlet-role-${part.role}`);
  return classes.join(' ');
}

// Arg type declared in the cmdlet metadata, falling back to `text`.
export function argType(meta, name) {
  for (const arg of (meta && meta.args) || []) {
    if (arg.name === name) return arg.type || 'text';
  }
  return 'text';
}

// Component factory: the read-only "chip" for one cmdlet. `form` selects the
// form of the per-arg child components (`compact` or `full`). When the cmdlet's
// metadata declares a display spec for this form (`meta.compact` /
// `meta.full`), the chip is rendered from that spec's parts (literal tokens and
// arg references); otherwise it falls back to the default "name args" rendering.
export function makeCmdlet(form) {
  const argComponent = `component-cmdlet-arg-${form}`;

  return {
    props: {
      cmdlet: { type: Object, default: null },
      cmdlets: { type: Array, default: () => [] },
    },

    setup(props) {
      const name = computed(() => props.cmdlet?.cmdlet || '');

      const meta = computed(() =>
        (props.cmdlets || []).find((c) => c.name === props.cmdlet?.cmdlet),
      );

      // Display spec for this form, or null when the cmdlet does not declare one
      // (then fall back to the default name+args rendering). An empty array is a
      // real spec that renders nothing.
      const spec = computed(() => {
        const value = meta.value && meta.value[form];
        return Array.isArray(value) ? value : null;
      });

      const argEntries = computed(() =>
        Object.entries(props.cmdlet?.args || {}).map(([argName, value]) => ({
          name: argName,
          value,
          type: argType(meta.value, argName),
        })),
      );

      function argValue(argName) {
        return (props.cmdlet?.args || {})[argName];
      }

      function valueComponentFor(argName) {
        return `component-cmdlet-arg-${argType(meta.value, argName)}-${form}`;
      }

      return { name, spec, argEntries, argValue, valueComponentFor, argComponent, partClasses };
    },

    template: `
<span class="apqa-cmdlet">
  <template v-if="spec !== null">
    <template v-for="(part, index) in spec" :key="index">
      <span v-if="'text' in part" :class="partClasses(part)">{{ part.text }}</span>
      <span v-else :class="partClasses(part)">
        <component :is="valueComponentFor(part.arg)" :value="argValue(part.arg)" />
      </span>
    </template>
  </template>
  <template v-else>
    <span class="apqa-cmdlet-part">{{ name }}</span>
    <template v-for="arg in argEntries" :key="arg.name">
      <span>{{ ' ' }}</span>
      <component :is="argComponent" :name="arg.name" :value="arg.value" :type="arg.type" />
    </template>
  </template>
</span>
`,
  };
}

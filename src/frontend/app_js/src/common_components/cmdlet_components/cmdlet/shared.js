import { computed } from 'vue';

import { getCmdletRenderer } from '../cmdlet_renderers';

import './styles.css';

// Pure text form of one cmdlet (used by the compact chip and as the source of
// the arg-part formatting shared with `cmdlet_arg`).
export function formatArgValue(value) {
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}

export function formatArgNameValue(name, value) {
  if (value === true) return name;
  return `${name}=${formatArgValue(value)}`;
}

export function formatArgs(args) {
  const parts = [];
  for (const [key, value] of Object.entries(args || {})) {
    parts.push(formatArgNameValue(key, value));
  }
  return parts;
}

export function cmdletParts(cmdlet) {
  const renderer = getCmdletRenderer(cmdlet?.cmdlet);
  const parts = renderer
    ? [renderer(cmdlet)]
    : [cmdlet?.cmdlet || '', ...formatArgs(cmdlet?.args)];
  return parts.filter((part) => part !== '');
}

export function cmdletText(cmdlet) {
  return cmdletParts(cmdlet).join(' ');
}

// Component factory: the read-only "chip" for one cmdlet. `form` selects the
// form of the per-arg child components (`compact` or `full`); both currently
// share this single implementation, with `full` intended to diverge later.
export function makeCmdlet(form) {
  const argComponent = `component-cmdlet-arg-${form}`;

  return {
    props: {
      cmdlet: { type: Object, default: null },
      cmdlets: { type: Array, default: () => [] },
    },

    setup(props) {
      const name = computed(() => props.cmdlet?.cmdlet || '');

      const wholePart = computed(() => {
        const renderer = getCmdletRenderer(props.cmdlet?.cmdlet);
        return renderer ? renderer(props.cmdlet) : null;
      });

      const argEntries = computed(() => {
        const meta = (props.cmdlets || []).find((c) => c.name === props.cmdlet?.cmdlet);
        const typeByName = Object.create(null);
        for (const arg of meta?.args || []) typeByName[arg.name] = arg.type || 'text';
        return Object.entries(props.cmdlet?.args || {}).map(([argName, value]) => ({
          name: argName,
          value,
          type: typeByName[argName] || 'text',
        }));
      });

      return { name, wholePart, argEntries, argComponent };
    },

    template: `
<span class="apqa-cmdlet">
  <template v-if="wholePart !== null">
    <span class="apqa-cmdlet-part">{{ wholePart }}</span>
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

import { computed } from 'vue';

// Registry of cmdlet renderers, keyed by cmdlet name. A renderer receives the
// stored cmdlet `{ cmdlet, args }` and returns the text to display. Cmdlets
// without a registered renderer fall back to the generic "name args" rendering.
const cmdletRenderers = Object.create(null);

export function registerCmdletRenderer(name, renderer) {
  cmdletRenderers[name] = renderer;
}

function formatArgValue(value) {
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}

function formatArgs(args) {
  const parts = [];
  for (const [key, value] of Object.entries(args || {})) {
    if (value === true) parts.push(key);
    else parts.push(`${key}=${formatArgValue(value)}`);
  }
  return parts;
}

// Display parts of a cmdlet: the name followed by each argument ("key=value"
// or a bare flag), or the opaque output of a custom renderer. Each part is
// rendered as its own no-wrap unit so the chain wraps between them (never in
// the middle of a word); overlong parts (e.g. a long path param) are cut with
// an ellipsis on the right.
export function cmdletParts(cmdlet) {
  const renderer = cmdletRenderers[cmdlet?.cmdlet];
  const parts = renderer
    ? [renderer(cmdlet)]
    : [cmdlet?.cmdlet || '', ...formatArgs(cmdlet?.args)];
  return parts.filter((part) => part !== '');
}

export function cmdletText(cmdlet) {
  return cmdletParts(cmdlet).join(' ');
}

// Built-in overrides.
// The `literal` cmdlet carries its value in `args.value`; render just the value
// itself, without the "literal value=" wording.
registerCmdletRenderer('literal', (cmdlet) => {
  const value = cmdlet?.args?.value;
  return value == null ? '' : String(value);
});

const Cmdlet = {
  props: ['cmdlet'],
  template: `
<span class="apqa-cmdlet">
  <template v-for="(part, index) in parts" :key="index">
    <span class="apqa-cmdlet-part">{{ part }}</span><span v-if="index < parts.length - 1">{{ ' ' }}</span>
  </template>
</span>
`,
  setup(props) {
    const parts = computed(() => cmdletParts(props.cmdlet));
    return { parts };
  },
};

export default Cmdlet;

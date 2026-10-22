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

function defaultCmdletText(cmdlet) {
  const name = cmdlet?.cmdlet || '';
  return [name, ...formatArgs(cmdlet?.args)].filter((part) => part !== '').join(' ');
}

export function cmdletText(cmdlet) {
  const renderer = cmdletRenderers[cmdlet?.cmdlet];
  return renderer ? renderer(cmdlet) : defaultCmdletText(cmdlet);
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
  template: `<span class="apqa-cmdlet">{{ text }}</span>`,
  setup(props) {
    const text = computed(() => cmdletText(props.cmdlet));
    return { text };
  },
};

export default Cmdlet;

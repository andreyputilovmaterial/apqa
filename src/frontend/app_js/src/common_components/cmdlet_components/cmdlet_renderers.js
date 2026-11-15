// Registry of cmdlet renderers, keyed by cmdlet name. A renderer receives the
// stored cmdlet `{ cmdlet, args }` and returns the text to display. Cmdlets
// without a registered renderer fall back to the generic "name args" rendering.
const cmdletRenderers = Object.create(null);

export function registerCmdletRenderer(name, renderer) {
  cmdletRenderers[name] = renderer;
}

export function getCmdletRenderer(name) {
  return cmdletRenderers[name];
}

// Built-in overrides.
// The `literal` cmdlet carries its value in `args.value`; render just the value
// itself, without the "literal value=" wording.
registerCmdletRenderer('literal', (cmdlet) => {
  const value = cmdlet?.args?.value;
  return value == null ? '' : String(value);
});

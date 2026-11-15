# InputMultipunch

Global multi-punch (multi-select) drop down, registered in `app.js` as
`component-input-multipunch`.

On click it expands a list of checkable options; clicking outside closes it.
The value is an array of the selected option values and works with `v-model`.

## Props

- `modelValue` (array) — the selected values.
- `options` (array) — the allowed values, either plain strings/numbers or
  `{ value, label }` objects.
- `placeholder` (string) — shown on the trigger when nothing is selected.
- `name` (string) — forwarded to each checkbox's `name` attribute.

Emits `update:modelValue` (for `v-model`) and `change`.

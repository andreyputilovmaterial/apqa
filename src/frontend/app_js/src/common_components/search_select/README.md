# SearchSelect

Single-select drop down with a search box, registered in `app.js` as
`component-search-select`.

The search box is focused automatically when the menu opens; typing filters the
options (case-insensitive substring match). Clicking an option selects it and
closes the menu; clicking outside or pressing Escape closes it. Arrow keys move
the highlight and Enter selects the highlighted option. The value is a single
option value (string or number) and works with `v-model`.

## Props

- `modelValue` (string | number | null) — the selected option value.
- `options` (array) — the allowed values, either plain strings/numbers or
  `{ value, label }` objects.
- `placeholder` (string) — shown on the trigger and search box when empty.
- `name` (string) — forwarded to a hidden input for form semantics.

Emits `update:modelValue` (for `v-model`), `change`, and `input`.

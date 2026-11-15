# InputRegexText

Text input with a regex toggle, registered in `app.js` as
`component-input-regextext`.

A normal-looking text box with a `.*` switch at the right inside the box. Regex
mode is **off by default**: the typed value filters by case-insensitive
substring (like a plain text input). Clicking the `.*` (it turns green) switches
to regular-expression matching (`new RegExp(text)`); an invalid expression while
typing matches nothing.

The value is `{ text, regex }` and works with `v-model`, mirroring how the
numeric/datetime range inputs emit `{ from, to }`.

## Props

- `modelValue` (string | number | object) — the current value. An object is
  read as `{ text, regex }`; a plain string/number is read as non-regex text.
- `value` (string | number | object) — Vue 2-style `:value` + `@input`
  alternative; `modelValue` takes precedence.
- `regexDefault` (boolean) — when the current value carries no explicit `regex`
  flag yet, this decides whether regex mode starts on. Default `false`.

Emits `update:modelValue` (for `v-model`), `input`, `change`, `focus`, and
`blur`. Native attributes like `placeholder` and `name` are forwarded to the
inner `<input>`; a `class` is applied to the wrapper.

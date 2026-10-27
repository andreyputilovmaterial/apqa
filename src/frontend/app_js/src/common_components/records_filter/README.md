# RecordsFilter

Reusable "filter + sort + paginate a list of records" component. Ported from the
`RecordsFilter.vue` component (and its `matchers.js`) used by the apphotoassistant
project selector, adapted to this repo's plain `.js` + `.css` Vue convention.

## Why two levels of filtering

Filtering happens at two levels:

1. **Which records are rendered** — the rendered list contains visible records
   plus records that were visible recently.
2. **Which records are shown** — records in the list that currently don't match
   are hidden with a CSS class (`.apqa-u-hidden`), not destroyed.

The point of level 2: while a user types quickly into a filter box, a record
that briefly disappears and then reappears is **not unmounted/recreated** — it
keeps its internal state and avoids re-fetching. A record that has stayed hidden
for more than 5 minutes is finally dropped from the rendered list (garbage
collected).

## API

Props:

- `columns` (object) — `{ key: label | { label, type, description, options } }`.
  One filter box per key. `type` is
  `'text' | 'number' | 'date' | 'datetime' | 'multipunch'` (default `text`).
  Non-text types render a range input, except `multipunch` which renders the
  globally registered `component-input-multipunch` drop down; a `multipunch` column
  should also provide `options` (the allowed values), e.g.
  `{ label: 'Tags', type: 'multipunch', options: ['counts', 'wave69'] }`.
  `description` is an optional docstring kept for a future per-column help
  message.
- `records` (array) — the source records.
- `keyField` (string) — unique key used to track per-record filter state.
- `needSort` (boolean) — enable the sort controls.
- `recordsPerPage` (number) — `0` = all on one page, `>0` = that many per page,
  otherwise default `25`.

Scoped slot:

- `#default="{ records }"` — the list to render. Each record carries
  `_filterMeta.cssClasses`; bind it to the rendered element's class so the
  "hide with CSS" level works:

  ```html
  <component-records-filter v-slot="{ records }" :columns="columns" :records="items" key-field="id" need-sort>
    <li v-for="item in records" :key="item.id" :class="item._filterMeta.cssClasses">
      …
    </li>
  </component-records-filter>
  ```

The component is registered locally by consumers (see
`app/qcrules_list/index.js`). For the number/date/datetime range inputs it uses
the globally registered `component-input-numericrange` and
`component-input-datetimerange` components; for `multipunch` columns it uses the
globally registered `component-input-multipunch` component.

## Collapsible header

The filter form starts **collapsed** into a single clickable header line so it
does not dominate the screen. Clicking the header expands the full set of
filter boxes plus the sort/pagination toolbar; clicking it again collapses back
to one line. The header always shows a short summary of the currently applied
filters (e.g. `Name: alps · Year: 2020..2025`), in both the collapsed and the
expanded state; when nothing is filtered it just reads `Filter`. The summary is
produced by the pure
`summarizeFilters(filters, columns)` helper in `matchers.js`, so it stays
testable without Vue.

## Matching & sorting

`matchers.js` holds the pure matching/sorting functions, kept free of Vue so they
can be unit-tested in isolation (`matchers.spec.js`).

Filter boxes are AND-ed together: a record must match every filled box. A
`multipunch` column follows the same rule internally — it matches only when the
record contains **all** of the selected values (an empty selection matches
everything).

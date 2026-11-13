# `common.css` changelog

Every change to `common.css` must be recorded here, in reverse-chronological
order, with the date and a short reason for the change. See
`.clinerules/09-frontend-common-css.md`.

## 2026-11-14

- Added a reusable `mdm-link-btn` class: a link styled as a bordered inline
  button (plain 1px `currentColor` border, transparent background, uniform
  padding, no underline/glow/outline, pointer cursor) that fades (350 ms ease)
  to the primary color on hover/focus/active. Used by the
  `background_onlineindicator` "reload the page" link (which overrides the
  hover/focus/active color to black).
- Increased the standard border-radius token `--mdm-border-radius` from 4px to
  7px (applies to `.mdm-btn`, `.mdmreport-control`, `.mdm-link-inline-btn`, and
  the new `.mdm-link-btn`), and made `.mdm-link-btn` use that token for its
  border radius.

## 2026-11-05

- Replaced the custom-drawn checkbox/radio box (a `::before` pseudo-element on
  `<input>`) with native controls tinted via `accent-color`. The old approach was
  misaligned in Chrome and invisible in Firefox (pseudo-elements are not supported
  on `<input>` there). Native controls render consistently across Chrome/Firefox/Safari.

## 2026-10-23

- Changed the primary color token `--mdm-color-primary` from purple `#6670bb`
  to green `#385` (hover shade `#217346`) per user request. Global change: the
  token feeds primary buttons, checked checkbox/radio states, and link-buttons,
  so those now render green.

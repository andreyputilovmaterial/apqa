# Dates & time

- **Store in UTC.** Dates and timestamps are stored in UTC in the backend
  (database). Full timestamps are ISO-8601 with an explicit UTC designator
  (`2025-07-15T10:00:00Z`); calendar dates with no time are `YYYY-MM-DD`.
- **Show in local time.** The frontend displays dates in the browser's local
  timezone. `new Date(isoString)` and the date formatting APIs already do the
  conversion — no manual timezone math.
- **User-entered dates are local.** A date entered by the user is interpreted in
  the browser's local timezone by default. Interpret it in a specific timezone
  (e.g. the trip's or the photo's local time) only when the UI/requirements
  explicitly capture that timezone.
- **No hardcoded dates.** Don't put dates in implementation code. Dates come
  from the database, or are generated when an object is created (e.g.
  `datetime.now(timezone.utc)`).

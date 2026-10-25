"""`as-date` — convert a value to a timezone-aware date/time."""

from datetime import date, datetime

from ..registry import cmdlets
from ..value_types import DateTime, PipeValue


@cmdlets.register('as-date')
def as_date(value: PipeValue, args: dict) -> DateTime:
    """Convert ``value`` to a timezone-aware ``datetime``.

    Accepts an already timezone-aware ``datetime`` (returned as-is) or an
    ISO-8601 text parsed with ``datetime.fromisoformat``. A naive datetime, a
    bare calendar date, or a text without a timezone fails with an explicit
    error, because a date/time without timezone information cannot be compared
    or ordered.
    """
    if isinstance(value, datetime):
        return _require_timezone(value)
    if isinstance(value, date):
        raise ValueError(
            'as-date: a calendar date has no time-of-day or timezone; provide '
            'a timezone-aware datetime (e.g. "2025-07-15T10:00:00Z")'
        )
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value)
        return _require_timezone(parsed)
    raise TypeError(
        f'as-date: cannot convert {type(value).__name__} to a date/time'
    )


def _require_timezone(dt):
    if dt.tzinfo is None:
        raise ValueError(
            f'as-date: {dt!r} has no timezone; a naive date/time is not '
            'allowed. Provide an explicit timezone or UTC offset (e.g. '
            '"2025-07-15T10:00:00Z").'
        )
    return dt

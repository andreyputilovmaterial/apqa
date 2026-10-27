"""`as-date` — convert a value to a timezone-aware date/time."""

import re
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from ..registry import cmdlets
from ..value_types import DateTime, PipeValue


@cmdlets.register(
    'as-date',
    kind='processor',
    args=[
        {
            'name': 'tz',
            'type': 'text',
            'required': False,
            'description': "IANA name or UTC offset used when the value has no timezone.",
        },
    ],
)
def as_date(value: PipeValue, args: dict) -> DateTime:
    """Convert ``value`` to a timezone-aware ``datetime``.

    Accepts an already timezone-aware ``datetime`` (returned as-is) or an
    ISO-8601 text parsed with ``datetime.fromisoformat``. A naive datetime or a
    text without a timezone uses ``args['tz']`` when provided — an IANA name
    (``"Europe/Berlin"``) or a UTC offset (``"+02:00"``, ``"Z"``) — and fails
    otherwise, because a date/time without timezone information cannot be
    compared or ordered. A bare calendar date (a ``date`` with no time-of-day)
    always fails.
    """
    if isinstance(value, datetime):
        return _with_timezone(value, args)
    if isinstance(value, date):
        raise ValueError(
            'as-date: a calendar date has no time-of-day; provide a full '
            'date/time (e.g. "2025-07-15T10:00:00" with a \'tz\' arg)'
        )
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value)
        return _with_timezone(parsed, args)
    raise TypeError(
        f'as-date: cannot convert {type(value).__name__} to a date/time'
    )


def _with_timezone(dt, args):
    if dt.tzinfo is not None:
        return dt
    tz = _timezone_from_arg(args)
    if tz is None:
        raise ValueError(
            f'as-date: {dt!r} has no timezone and no \'tz\' arg was provided; '
            'a naive date/time is not allowed. Provide "tz" (e.g. '
            '"Europe/Berlin" or "+02:00") or a value with a UTC offset.'
        )
    return dt.replace(tzinfo=tz)


def _timezone_from_arg(args):
    raw = args.get('tz')
    if raw is None or raw == '':
        return None
    tz = _parse_timezone(str(raw))
    if tz is None:
        raise ValueError(
            f"as-date: invalid 'tz' arg {raw!r}; use an IANA name (e.g. "
            '"Europe/Berlin") or a UTC offset (e.g. "+02:00")'
        )
    return tz


def _parse_timezone(text):
    try:
        return ZoneInfo(text)
    except Exception:
        pass
    if text == 'Z':
        return timezone.utc
    match = re.fullmatch(r'([+-])(\d{1,2})(?::?(\d{2}))?', text)
    if match is None:
        return None
    sign, hours, minutes = match.groups()
    total_minutes = int(hours) * 60 + int(minutes or 0)
    if sign == '-':
        total_minutes = -total_minutes
    return timezone(timedelta(minutes=total_minutes))


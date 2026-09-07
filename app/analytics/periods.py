"""Resolves a `period` query parameter (or explicit start/end) into a
half-open UTC window [start, end)."""

from datetime import UTC, datetime, timedelta

VALID_PERIODS = {"hourly", "daily", "weekly", "monthly"}


def resolve_window(
    period: str | None,
    start: datetime | None,
    end: datetime | None,
    now: datetime | None = None,
) -> tuple[datetime, datetime]:
    if start is not None and end is not None:
        return _to_utc(start), _to_utc(end)

    reference = now or datetime.now(UTC)
    reference = _to_utc(reference)

    if period == "hourly":
        window_start = reference.replace(minute=0, second=0, microsecond=0)
        return window_start, window_start + timedelta(hours=1)
    if period == "weekly":
        # ISO week: Monday 00:00 through next Monday 00:00
        day_start = reference.replace(hour=0, minute=0, second=0, microsecond=0)
        window_start = day_start - timedelta(days=day_start.weekday())
        return window_start, window_start + timedelta(days=7)
    if period == "monthly":
        day_start = reference.replace(hour=0, minute=0, second=0, microsecond=0)
        window_start = day_start.replace(day=1)
        if window_start.month == 12:
            window_end = window_start.replace(year=window_start.year + 1, month=1)
        else:
            window_end = window_start.replace(month=window_start.month + 1)
        return window_start, window_end

    # default: daily
    window_start = reference.replace(hour=0, minute=0, second=0, microsecond=0)
    return window_start, window_start + timedelta(days=1)


def _to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)

from datetime import UTC, datetime

from app.analytics.periods import resolve_window


def test_daily_window() -> None:
    now = datetime(2026, 9, 6, 15, 30, tzinfo=UTC)
    start, end = resolve_window("daily", None, None, now=now)
    assert start == datetime(2026, 9, 6, 0, 0, tzinfo=UTC)
    assert end == datetime(2026, 9, 7, 0, 0, tzinfo=UTC)


def test_weekly_window_starts_monday() -> None:
    # 2026-09-06 is a Sunday
    now = datetime(2026, 9, 6, 15, 30, tzinfo=UTC)
    start, end = resolve_window("weekly", None, None, now=now)
    assert start.weekday() == 0
    assert start == datetime(2026, 8, 31, 0, 0, tzinfo=UTC)
    assert (end - start).days == 7


def test_monthly_window_handles_year_rollover() -> None:
    now = datetime(2026, 12, 15, tzinfo=UTC)
    start, end = resolve_window("monthly", None, None, now=now)
    assert start == datetime(2026, 12, 1, tzinfo=UTC)
    assert end == datetime(2027, 1, 1, tzinfo=UTC)


def test_explicit_start_end_overrides_period() -> None:
    start_in = datetime(2026, 1, 1, tzinfo=UTC)
    end_in = datetime(2026, 1, 2, tzinfo=UTC)
    start, end = resolve_window(None, start_in, end_in)
    assert start == start_in
    assert end == end_in


def test_naive_explicit_bounds_are_treated_as_utc() -> None:
    start, end = resolve_window(None, datetime(2026, 1, 1), datetime(2026, 1, 2))
    assert start.tzinfo is not None
    assert end.tzinfo is not None

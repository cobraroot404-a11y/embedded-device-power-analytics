from datetime import UTC, datetime, timedelta

from app.analytics.state_duration import TelemetryPoint
from app.analytics.timeline import build_timeline

GAP = timedelta(minutes=30)
NO_GAP = timedelta(hours=24)


def _dt(y, m, d, h, mi=0) -> datetime:
    return datetime(y, m, d, h, mi, tzinfo=UTC)


def test_basic_segments_match_spec_example() -> None:
    points = [
        TelemetryPoint(_dt(2026, 9, 6, 8, 0), "ON"),
        TelemetryPoint(_dt(2026, 9, 6, 8, 45), "SLEEP"),
        TelemetryPoint(_dt(2026, 9, 6, 9, 15), "ON"),
        TelemetryPoint(_dt(2026, 9, 6, 10, 0), "OFF"),
    ]
    segments, reboots = build_timeline(points, _dt(2026, 9, 6, 8, 0), _dt(2026, 9, 6, 10, 0), NO_GAP)

    assert [s.state for s in segments] == ["ON", "SLEEP", "ON"]
    assert segments[0].start == _dt(2026, 9, 6, 8, 0)
    assert segments[0].end == _dt(2026, 9, 6, 8, 45)
    assert reboots == []


def test_gap_becomes_unknown_segment() -> None:
    points = [
        TelemetryPoint(_dt(2026, 9, 6, 8, 0), "ON"),
        TelemetryPoint(_dt(2026, 9, 6, 9, 30), "ON"),
    ]
    segments, _ = build_timeline(points, _dt(2026, 9, 6, 8, 0), _dt(2026, 9, 6, 9, 30), GAP)
    assert len(segments) == 1
    assert segments[0].state == "UNKNOWN"
    assert segments[0].reason == "gap"


def test_reboot_produces_marker_and_unknown_segment() -> None:
    points = [
        TelemetryPoint(_dt(2026, 9, 6, 8, 0), "ON", boot_id="a"),
        TelemetryPoint(_dt(2026, 9, 6, 8, 10), "ON", boot_id="b"),
    ]
    segments, reboots = build_timeline(points, _dt(2026, 9, 6, 8, 0), _dt(2026, 9, 6, 8, 10), GAP)
    assert segments[0].state == "UNKNOWN"
    assert segments[0].reason == "reboot"
    assert len(reboots) == 1
    assert reboots[0].at == _dt(2026, 9, 6, 8, 10)


def test_empty_points_produce_single_no_data_segment() -> None:
    segments, reboots = build_timeline([], _dt(2026, 9, 6, 0, 0), _dt(2026, 9, 7, 0, 0), GAP)
    assert len(segments) == 1
    assert segments[0].reason == "no_data"
    assert reboots == []

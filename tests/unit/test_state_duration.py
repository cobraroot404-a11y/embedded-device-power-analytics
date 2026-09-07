from datetime import UTC, datetime, timedelta

from app.analytics.energy import estimate_energy
from app.analytics.state_duration import (
    DurationResult,
    TelemetryPoint,
    compute_state_durations,
)

GAP = timedelta(minutes=30)
# A deliberately large threshold for tests that are exercising pure interval
# attribution/boundary-clipping math and use event spacing wider than the
# real 30-minute default (which is tested on its own terms separately, in
# test_communication_gap_excluded_from_classified_time) — this keeps the two
# concerns (duration attribution vs. gap classification) from interfering.
NO_GAP = timedelta(hours=24)


def _dt(y, m, d, h, mi=0) -> datetime:
    return datetime(y, m, d, h, mi, tzinfo=UTC)


def test_spec_example_on_sleep_off_durations() -> None:
    # 08:00 ON, 08:45 SLEEP, 09:15 ON, 10:00 OFF -> ON=90m, SLEEP=30m, OFF=0
    points = [
        TelemetryPoint(_dt(2026, 9, 6, 8, 0), "ON"),
        TelemetryPoint(_dt(2026, 9, 6, 8, 45), "SLEEP"),
        TelemetryPoint(_dt(2026, 9, 6, 9, 15), "ON"),
        TelemetryPoint(_dt(2026, 9, 6, 10, 0), "OFF"),
    ]
    result = compute_state_durations(points, _dt(2026, 9, 6, 8, 0), _dt(2026, 9, 6, 10, 0), NO_GAP)

    assert result.on_seconds == 90 * 60
    assert result.sleep_seconds == 30 * 60
    assert result.off_seconds == 0
    assert result.usage_percent == 75.0
    assert result.power_saving_percent == 25.0


def test_midnight_boundary_split() -> None:
    # 23:50 ON -> 00:20 SLEEP next day: 10 min to day1, 20 min to day2
    on_event = TelemetryPoint(_dt(2026, 9, 6, 23, 50), "ON")
    sleep_event = TelemetryPoint(_dt(2026, 9, 7, 0, 20), "SLEEP")

    day1_start, day1_end = _dt(2026, 9, 6, 0, 0), _dt(2026, 9, 7, 0, 0)
    day1_result = compute_state_durations([on_event, sleep_event], day1_start, day1_end, GAP)
    assert day1_result.on_seconds == 10 * 60

    day2_start, day2_end = _dt(2026, 9, 7, 0, 0), _dt(2026, 9, 8, 0, 0)
    day2_result = compute_state_durations([on_event, sleep_event], day2_start, day2_end, GAP)
    assert day2_result.on_seconds == 20 * 60


def test_communication_gap_excluded_from_classified_time() -> None:
    points = [
        TelemetryPoint(_dt(2026, 9, 6, 8, 0), "ON"),
        TelemetryPoint(_dt(2026, 9, 6, 9, 30), "ON"),  # 90 min later: exceeds 30 min gap threshold
    ]
    result = compute_state_durations(points, _dt(2026, 9, 6, 8, 0), _dt(2026, 9, 6, 9, 30), GAP)

    assert result.on_seconds == 0
    assert result.unknown_seconds == 90 * 60
    assert result.gap_count == 1
    assert result.classified_seconds == 0
    assert result.usage_percent is None  # zero denominator handled safely


def test_reboot_boundary_is_unknown_not_continuous() -> None:
    points = [
        TelemetryPoint(_dt(2026, 9, 6, 8, 0), "ON", boot_id="boot-a"),
        TelemetryPoint(_dt(2026, 9, 6, 8, 10), "ON", boot_id="boot-b"),
    ]
    result = compute_state_durations(points, _dt(2026, 9, 6, 8, 0), _dt(2026, 9, 6, 8, 10), GAP)

    assert result.on_seconds == 0
    assert result.unknown_seconds == 10 * 60
    assert result.reboot_count == 1


def test_no_duration_manufactured_after_last_event() -> None:
    points = [TelemetryPoint(_dt(2026, 9, 6, 8, 0), "ON")]
    result = compute_state_durations(points, _dt(2026, 9, 6, 8, 0), _dt(2026, 9, 6, 12, 0), GAP)

    assert result.on_seconds == 0
    assert result.unknown_seconds == 4 * 3600


def test_no_duration_manufactured_before_first_event() -> None:
    # A second (OFF) point bounds the ON interval; nothing follows OFF, so
    # the tail past it is unknown too (never manufactured), per
    # test_no_duration_manufactured_after_last_event above.
    points = [
        TelemetryPoint(_dt(2026, 9, 6, 10, 0), "ON"),
        TelemetryPoint(_dt(2026, 9, 6, 11, 0), "OFF"),
    ]
    result = compute_state_durations(points, _dt(2026, 9, 6, 8, 0), _dt(2026, 9, 6, 12, 0), NO_GAP)

    assert result.unknown_seconds == 3 * 3600  # 08:00-10:00 and 11:00-12:00
    assert result.on_seconds == 3600  # 10:00-11:00
    assert result.off_seconds == 0


def test_zero_duration_transition_is_not_double_counted() -> None:
    points = [
        TelemetryPoint(_dt(2026, 9, 6, 8, 0), "ON"),
        TelemetryPoint(_dt(2026, 9, 6, 8, 0), "SLEEP"),  # identical timestamp
        TelemetryPoint(_dt(2026, 9, 6, 8, 30), "SLEEP"),
    ]
    result = compute_state_durations(points, _dt(2026, 9, 6, 8, 0), _dt(2026, 9, 6, 8, 30), GAP)

    assert result.sleep_seconds == 30 * 60
    assert result.on_seconds == 0


def test_empty_device_window_is_entirely_unknown() -> None:
    result = compute_state_durations([], _dt(2026, 9, 6, 0, 0), _dt(2026, 9, 7, 0, 0), GAP)
    assert result.unknown_seconds == 24 * 3600
    assert result.usage_percent is None
    assert result.power_saving_percent is None


def test_out_of_order_points_are_sorted_before_attribution() -> None:
    points = [
        TelemetryPoint(_dt(2026, 9, 6, 9, 0), "SLEEP"),
        TelemetryPoint(_dt(2026, 9, 6, 8, 0), "ON"),  # arrives "later" but happened first
    ]
    result = compute_state_durations(points, _dt(2026, 9, 6, 8, 0), _dt(2026, 9, 6, 9, 0), NO_GAP)
    assert result.on_seconds == 3600


def test_max_on_streak_tracks_longest_continuous_on_run() -> None:
    points = [
        TelemetryPoint(_dt(2026, 9, 6, 0, 0), "ON"),
        TelemetryPoint(_dt(2026, 9, 6, 2, 0), "ON"),
        TelemetryPoint(_dt(2026, 9, 6, 9, 0), "SLEEP"),  # 9h continuous ON streak
        TelemetryPoint(_dt(2026, 9, 6, 10, 0), "ON"),
        TelemetryPoint(_dt(2026, 9, 6, 10, 30), "OFF"),  # only 30m streak
    ]
    result = compute_state_durations(points, _dt(2026, 9, 6, 0, 0), _dt(2026, 9, 6, 10, 30), NO_GAP)
    assert result.max_on_streak_seconds == 9 * 3600


def test_energy_estimate_uses_observed_power_only() -> None:
    result = DurationResult(on_seconds=3600, sleep_seconds=7200)
    result.on_power_samples = [10.0]
    result.sleep_power_samples = [1.0]
    estimate = estimate_energy(result)

    assert estimate.on_avg_power_watts == 10.0
    assert estimate.sleep_avg_power_watts == 1.0
    assert estimate.off_avg_power_watts is None
    # (10W * 1h + 1W * 2h) / 1000 = 0.012 kWh
    assert round(estimate.estimated_energy_kwh, 6) == 0.012


def test_energy_estimate_none_when_no_power_samples() -> None:
    result = DurationResult(on_seconds=3600)
    estimate = estimate_energy(result)
    assert estimate.estimated_energy_kwh is None

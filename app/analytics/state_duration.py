"""Interval-based state-duration analytics.

Telemetry events represent *state transitions*, not samples of equal weight —
duration must come from the elapsed wall-clock time between consecutive
device-timestamped events, never from message counts. This module is the
single place that rule is enforced.

Methodology (see README "Analytics Methodology" for the narrative version):

1. Events are sorted by device event time (`time`), not ingestion order, so
   out-of-order delivery cannot corrupt duration attribution.
2. The interval between two consecutive events [p1, p2) is attributed to
   `p1.state` for its duration, UNLESS:
     - `boot_id` changed between p1 and p2 (a reboot/new session occurred
       somewhere in that interval — we cannot assume uninterrupted operation
       across a reboot boundary), or
     - the raw gap between p1 and p2 exceeds `gap_threshold` (a communication
       gap — we do not know what happened during a silence, so we do not
       classify it as the prior state).
   In both cases the interval is classified UNKNOWN instead.
3. Each interval is clipped to the requested [window_start, window_end)
   before being attributed, which is what makes an interval crossing
   midnight/week/month boundaries split correctly across two adjacent
   period queries.
4. Time before the first known event, or after the last known event, is
   UNKNOWN. Duration is never manufactured/extrapolated past the edges of
   what telemetry actually reported. Callers that want a bounded interval to
   participate in tail/head clipping must include the nearest event just
   outside the window in `points` (the repository layer does this).
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta

ON = "ON"
SLEEP = "SLEEP"
OFF = "OFF"


@dataclass(frozen=True, slots=True)
class TelemetryPoint:
    time: datetime
    state: str
    boot_id: str | None = None
    power_watts: float | None = None


@dataclass(slots=True)
class DurationResult:
    on_seconds: float = 0.0
    sleep_seconds: float = 0.0
    off_seconds: float = 0.0
    unknown_seconds: float = 0.0
    gap_seconds: float = 0.0
    gap_count: int = 0
    reboot_count: int = 0
    max_on_streak_seconds: float = 0.0
    on_power_samples: list[float] = field(default_factory=list)
    sleep_power_samples: list[float] = field(default_factory=list)
    off_power_samples: list[float] = field(default_factory=list)

    @property
    def classified_seconds(self) -> float:
        return self.on_seconds + self.sleep_seconds + self.off_seconds

    @property
    def usage_percent(self) -> float | None:
        if self.classified_seconds <= 0:
            return None
        return (self.on_seconds / self.classified_seconds) * 100.0

    @property
    def power_saving_percent(self) -> float | None:
        if self.classified_seconds <= 0:
            return None
        return ((self.sleep_seconds + self.off_seconds) / self.classified_seconds) * 100.0


def compute_state_durations(
    points: list[TelemetryPoint],
    window_start: datetime,
    window_end: datetime,
    gap_threshold: timedelta,
) -> DurationResult:
    result = DurationResult()

    if window_end <= window_start:
        return result

    if not points:
        result.unknown_seconds = (window_end - window_start).total_seconds()
        return result

    pts = sorted(points, key=lambda p: p.time)

    if pts[0].time > window_start:
        result.unknown_seconds += (min(pts[0].time, window_end) - window_start).total_seconds()

    current_on_streak = 0.0

    def _close_on_streak() -> None:
        nonlocal current_on_streak
        result.max_on_streak_seconds = max(result.max_on_streak_seconds, current_on_streak)
        current_on_streak = 0.0

    for i in range(len(pts) - 1):
        p1, p2 = pts[i], pts[i + 1]
        if p2.time <= p1.time:
            continue  # non-positive interval: duplicate/identical timestamp, nothing to attribute

        clipped_start = max(p1.time, window_start)
        clipped_end = min(p2.time, window_end)
        if clipped_end <= clipped_start:
            continue  # this segment doesn't overlap the requested window at all

        duration = (clipped_end - clipped_start).total_seconds()
        is_reboot = bool(p1.boot_id) and bool(p2.boot_id) and p1.boot_id != p2.boot_id
        is_gap = (p2.time - p1.time) > gap_threshold

        if is_reboot:
            result.unknown_seconds += duration
            result.reboot_count += 1
            _close_on_streak()
        elif is_gap:
            result.unknown_seconds += duration
            result.gap_seconds += duration
            result.gap_count += 1
            _close_on_streak()
        else:
            _attribute(result, p1.state, duration, p1.power_watts)
            if p1.state == ON:
                current_on_streak += duration
            else:
                _close_on_streak()

    _close_on_streak()

    if pts[-1].time < window_end:
        tail_start = max(pts[-1].time, window_start)
        result.unknown_seconds += (window_end - tail_start).total_seconds()

    return result


def _attribute(result: DurationResult, state: str, duration: float, power_watts: float | None) -> None:
    if state == ON:
        result.on_seconds += duration
        if power_watts is not None:
            result.on_power_samples.append(power_watts)
    elif state == SLEEP:
        result.sleep_seconds += duration
        if power_watts is not None:
            result.sleep_power_samples.append(power_watts)
    elif state == OFF:
        result.off_seconds += duration
        if power_watts is not None:
            result.off_power_samples.append(power_watts)

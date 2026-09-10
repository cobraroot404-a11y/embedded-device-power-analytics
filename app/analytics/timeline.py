"""Segment-level view of the same interval logic used by state_duration.py,
for rendering a device's state timeline rather than aggregating totals."""

from dataclasses import dataclass
from datetime import datetime, timedelta

from app.analytics.state_duration import OFF, ON, SLEEP, TelemetryPoint

UNKNOWN = "UNKNOWN"


@dataclass(slots=True)
class TimelineSegment:
    start: datetime
    end: datetime
    state: str
    reason: str | None = None


@dataclass(slots=True)
class RebootMarker:
    at: datetime


def build_timeline(
    points: list[TelemetryPoint],
    window_start: datetime,
    window_end: datetime,
    gap_threshold: timedelta,
) -> tuple[list[TimelineSegment], list[RebootMarker]]:
    segments: list[TimelineSegment] = []
    reboots: list[RebootMarker] = []

    if window_end <= window_start:
        return segments, reboots

    if not points:
        segments.append(TimelineSegment(window_start, window_end, UNKNOWN, "no_data"))
        return segments, reboots

    pts = sorted(points, key=lambda p: p.time)

    if pts[0].time > window_start:
        segments.append(TimelineSegment(window_start, min(pts[0].time, window_end), UNKNOWN, "no_data"))

    for i in range(len(pts) - 1):
        p1, p2 = pts[i], pts[i + 1]
        if p2.time <= p1.time:
            continue

        clipped_start = max(p1.time, window_start)
        clipped_end = min(p2.time, window_end)
        if clipped_end <= clipped_start:
            continue

        is_reboot = bool(p1.boot_id) and bool(p2.boot_id) and p1.boot_id != p2.boot_id
        is_gap = (p2.time - p1.time) > gap_threshold

        if is_reboot:
            segments.append(TimelineSegment(clipped_start, clipped_end, UNKNOWN, "reboot"))
            if window_start <= p2.time <= window_end:
                reboots.append(RebootMarker(p2.time))
        elif is_gap:
            segments.append(TimelineSegment(clipped_start, clipped_end, UNKNOWN, "gap"))
        else:
            state = p1.state if p1.state in (ON, SLEEP, OFF) else UNKNOWN
            segments.append(TimelineSegment(clipped_start, clipped_end, state, None))

    if pts[-1].time < window_end:
        segments.append(
            TimelineSegment(max(pts[-1].time, window_start), window_end, UNKNOWN, "no_data")
        )

    return segments, reboots

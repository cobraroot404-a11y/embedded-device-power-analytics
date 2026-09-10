from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.anomalies import detect_period_anomalies
from app.analytics.energy import estimate_energy
from app.analytics.periods import resolve_window
from app.analytics.state_duration import compute_state_durations
from app.analytics.timeline import build_timeline
from app.core.config import Settings
from app.models.device import Device
from app.schemas.analytics import (
    AnomalySummary,
    DeviceAnalytics,
    DevicePowerSummary,
    DeviceTimeline,
    FleetHealthDistribution,
    FleetOverview,
    FleetPowerAnalytics,
    FleetStates,
    FleetSummary,
    FleetUsageTrend,
    FleetUsageTrendPoint,
    PowerTrendPoint,
    TimelineSegmentOut,
)
from app.services import telemetry_repository as repo


def is_device_active(device: Device, settings: Settings, now: datetime) -> bool:
    inactivity_threshold = timedelta(minutes=settings.gap_threshold_minutes * 2)
    return (now - device.last_seen) <= inactivity_threshold


async def compute_device_analytics(
    session: AsyncSession,
    device_id: str,
    period: str | None,
    start: datetime | None,
    end: datetime | None,
    settings: Settings,
) -> DeviceAnalytics:
    window_start, window_end = resolve_window(period, start, end)
    points = await repo.get_points_for_window(session, device_id, window_start, window_end)
    result = compute_state_durations(
        points, window_start, window_end, timedelta(seconds=settings.gap_threshold_seconds)
    )
    energy = estimate_energy(result)

    return DeviceAnalytics(
        device_id=device_id,
        period=period or "custom",
        window_start=window_start,
        window_end=window_end,
        on_seconds=result.on_seconds,
        sleep_seconds=result.sleep_seconds,
        off_seconds=result.off_seconds,
        unknown_seconds=result.unknown_seconds,
        classified_seconds=result.classified_seconds,
        usage_percent=result.usage_percent,
        power_saving_percent=result.power_saving_percent,
        communication_gap_count=result.gap_count,
        communication_gap_seconds=result.gap_seconds,
        reboot_count=result.reboot_count,
        on_avg_power_watts=energy.on_avg_power_watts,
        sleep_avg_power_watts=energy.sleep_avg_power_watts,
        off_avg_power_watts=energy.off_avg_power_watts,
        estimated_energy_kwh=energy.estimated_energy_kwh,
    )


async def record_period_anomalies(
    session: AsyncSession, device_id: str, analytics: DeviceAnalytics, settings: Settings
) -> None:
    """Persists rule-based anomalies derived from a computed analytics window
    (called from the API on read is intentionally avoided; ingestion-time
    anomalies are the source of truth — this helper exists for batch/manual
    re-evaluation and is not wired into the hot read path)."""
    from app.analytics.state_duration import DurationResult

    result = DurationResult(
        on_seconds=analytics.on_seconds,
        sleep_seconds=analytics.sleep_seconds,
        off_seconds=analytics.off_seconds,
        unknown_seconds=analytics.unknown_seconds,
        gap_seconds=analytics.communication_gap_seconds,
        gap_count=analytics.communication_gap_count,
        reboot_count=analytics.reboot_count,
    )
    now = datetime.now(UTC)
    findings = detect_period_anomalies(device_id, result, settings, now, analytics.window_end)
    for finding in findings:
        await repo.insert_anomaly(
            session,
            device_id=device_id,
            anomaly_type=finding.anomaly_type,
            detected_at=finding.detected_at,
            event_time=finding.event_time,
            details=finding.details,
        )
    await session.commit()


async def compute_fleet_summary(
    session: AsyncSession,
    period: str | None,
    start: datetime | None,
    end: datetime | None,
    settings: Settings,
) -> FleetSummary:
    devices = await repo.list_devices(session)
    now = datetime.now(UTC)
    window_start, window_end = resolve_window(period, start, end)

    per_device: list[dict] = []
    total_energy = 0.0
    have_energy = False
    anomaly_since = now - timedelta(days=1)

    for device in devices:
        analytics = await compute_device_analytics(session, device.device_id, period, start, end, settings)
        anomaly_count = await repo.count_anomalies_for_device(session, device.device_id, anomaly_since)
        entry = {
            "device_id": device.device_id,
            "usage_percent": analytics.usage_percent,
            "power_saving_percent": analytics.power_saving_percent,
            "communication_gap_count": analytics.communication_gap_count,
            "is_active": is_device_active(device, settings, now),
            "estimated_energy_kwh": analytics.estimated_energy_kwh,
            "anomaly_count": anomaly_count,
            "on_seconds": analytics.on_seconds,
            "sleep_seconds": analytics.sleep_seconds,
            "off_seconds": analytics.off_seconds,
            "unknown_seconds": analytics.unknown_seconds,
        }
        per_device.append(entry)
        if analytics.estimated_energy_kwh is not None:
            total_energy += analytics.estimated_energy_kwh
            have_energy = True

    active_devices = sum(1 for d in per_device if d["is_active"])
    usage_values = [d["usage_percent"] for d in per_device if d["usage_percent"] is not None]
    saving_values = [d["power_saving_percent"] for d in per_device if d["power_saving_percent"] is not None]

    ranked_by_usage = sorted(
        (d for d in per_device if d["usage_percent"] is not None),
        key=lambda d: d["usage_percent"],
        reverse=True,
    )
    inefficient = [
        d
        for d in per_device
        if d["usage_percent"] is not None and d["usage_percent"] < settings.rarely_used_on_percent
    ]
    with_gaps = [d for d in per_device if d["communication_gap_count"] > 0]

    recent_since = now - timedelta(days=1)
    total_anomalies_recent = await repo.count_recent_anomalies(session, recent_since)

    return FleetSummary(
        total_devices=len(devices),
        active_devices=active_devices,
        average_usage_percent=(sum(usage_values) / len(usage_values)) if usage_values else None,
        average_power_saving_percent=(sum(saving_values) / len(saving_values)) if saving_values else None,
        highest_usage_devices=ranked_by_usage[:5],
        lowest_usage_devices=list(reversed(ranked_by_usage))[:5],
        inefficient_devices=inefficient,
        devices_with_gaps=with_gaps,
        all_devices=per_device,
        total_anomalies_recent=total_anomalies_recent,
        estimated_fleet_energy_kwh=total_energy if have_energy else None,
        period=period or "custom",
        window_start=window_start,
        window_end=window_end,
    )


async def get_device_timeline(
    session: AsyncSession,
    device_id: str,
    period: str | None,
    start: datetime | None,
    end: datetime | None,
    settings: Settings,
) -> DeviceTimeline:
    window_start, window_end = resolve_window(period, start, end)
    points = await repo.get_points_for_window(session, device_id, window_start, window_end)
    segments, reboots = build_timeline(
        points, window_start, window_end, timedelta(seconds=settings.gap_threshold_seconds)
    )
    return DeviceTimeline(
        device_id=device_id,
        window_start=window_start,
        window_end=window_end,
        segments=[
            TimelineSegmentOut(start=s.start, end=s.end, state=s.state, reason=s.reason)
            for s in segments
        ],
        reboots=[r.at for r in reboots],
    )


async def get_fleet_states(session: AsyncSession) -> FleetStates:
    devices = await repo.list_devices(session)
    counts = {"ON": 0, "SLEEP": 0, "OFF": 0, "UNKNOWN": 0}
    for d in devices:
        counts[d.last_state if d.last_state in counts else "UNKNOWN"] += 1
    return FleetStates(
        on=counts["ON"], sleep=counts["SLEEP"], off=counts["OFF"], unknown=counts["UNKNOWN"],
        total=len(devices),
    )


async def get_fleet_health(
    session: AsyncSession, settings: Settings, now: datetime
) -> FleetHealthDistribution:
    """Deterministic health classification, derived from the same signals as
    the anomaly engine (communication recency + recent anomaly severity) —
    never a fabricated or hardcoded status."""
    from app.analytics.severity import CRITICAL, get_severity

    devices = await repo.list_devices(session)
    since = now - timedelta(hours=24)
    healthy = warning = critical = offline = 0

    for device in devices:
        if not is_device_active(device, settings, now):
            offline += 1
            continue
        anomalies = await repo.list_anomalies(session, device.device_id, limit=20)
        recent = [a for a in anomalies if a.detected_at >= since]
        severities = [get_severity(a.anomaly_type, a.details) for a in recent]
        if CRITICAL in severities:
            critical += 1
        elif severities:
            warning += 1
        else:
            healthy += 1

    return FleetHealthDistribution(healthy=healthy, warning=warning, critical=critical, offline=offline)


def _resolve_trend_buckets(
    window_start: datetime, window_end: datetime
) -> list[tuple[datetime, datetime]]:
    span = window_end - window_start
    bucket_size = timedelta(hours=1) if span <= timedelta(hours=48) else timedelta(days=1)
    buckets = []
    cursor = window_start
    while cursor < window_end:
        next_cursor = min(cursor + bucket_size, window_end)
        buckets.append((cursor, next_cursor))
        cursor = next_cursor
    return buckets


async def get_fleet_usage_trend(
    session: AsyncSession,
    period: str | None,
    start: datetime | None,
    end: datetime | None,
    settings: Settings,
) -> FleetUsageTrend:
    window_start, window_end = resolve_window(period, start, end)
    devices = await repo.list_devices(session)
    gap = timedelta(seconds=settings.gap_threshold_seconds)

    device_points = {
        d.device_id: await repo.get_points_for_window(session, d.device_id, window_start, window_end)
        for d in devices
    }

    points_out = []
    for bucket_start, bucket_end in _resolve_trend_buckets(window_start, window_end):
        on_total = sleep_total = off_total = unknown_total = 0.0
        for points in device_points.values():
            result = compute_state_durations(points, bucket_start, bucket_end, gap)
            on_total += result.on_seconds
            sleep_total += result.sleep_seconds
            off_total += result.off_seconds
            unknown_total += result.unknown_seconds
        classified = on_total + sleep_total + off_total
        usage_pct = (on_total / classified * 100) if classified > 0 else None
        saving_pct = ((sleep_total + off_total) / classified * 100) if classified > 0 else None
        points_out.append(
            FleetUsageTrendPoint(
                bucket_start=bucket_start,
                usage_percent=usage_pct,
                power_saving_percent=saving_pct,
                classified_seconds=classified,
                unknown_seconds=unknown_total,
            )
        )

    return FleetUsageTrend(
        period=period or "custom", window_start=window_start, window_end=window_end, points=points_out
    )


async def get_fleet_power_analytics(
    session: AsyncSession,
    period: str | None,
    start: datetime | None,
    end: datetime | None,
    settings: Settings,
) -> FleetPowerAnalytics:
    window_start, window_end = resolve_window(period, start, end)
    devices = await repo.list_devices(session)

    device_summaries = []
    total_energy = 0.0
    have_energy = False
    for device in devices:
        analytics = await compute_device_analytics(
            session, device.device_id, period, start, end, settings
        )
        avg_power = None
        powers = [
            p
            for p in (
                analytics.on_avg_power_watts,
                analytics.sleep_avg_power_watts,
                analytics.off_avg_power_watts,
            )
            if p is not None
        ]
        if powers:
            avg_power = sum(powers) / len(powers)
        device_summaries.append(
            DevicePowerSummary(
                device_id=device.device_id,
                avg_power_watts=avg_power,
                estimated_energy_kwh=analytics.estimated_energy_kwh,
                battery_percent=None,
            )
        )
        if analytics.estimated_energy_kwh is not None:
            total_energy += analytics.estimated_energy_kwh
            have_energy = True

    bucket = "hour" if (window_end - window_start) <= timedelta(hours=48) else "day"
    trend_rows = await repo.get_power_trend(session, window_start, window_end, bucket)
    trend = [PowerTrendPoint(bucket_start=b, avg_power_watts=v) for b, v in trend_rows]

    return FleetPowerAnalytics(
        period=period or "custom",
        window_start=window_start,
        window_end=window_end,
        devices=device_summaries,
        trend=trend,
        estimated_fleet_energy_kwh=total_energy if have_energy else None,
    )


async def get_fleet_overview(
    session: AsyncSession,
    period: str | None,
    start: datetime | None,
    end: datetime | None,
    settings: Settings,
) -> FleetOverview:
    now = datetime.now(UTC)
    summary = await compute_fleet_summary(session, period, start, end, settings)
    states = await get_fleet_states(session)
    health = await get_fleet_health(session, settings, now)
    return FleetOverview(summary=summary, states=states, health=health)


async def get_anomaly_summary(session: AsyncSession, since: datetime) -> AnomalySummary:
    counts = await repo.count_anomalies_by_type(session, since)
    return AnomalySummary(
        total_active=sum(counts.values()),
        communication_gaps=counts.get("communication_gap", 0),
        power_warnings=counts.get("abnormal_power", 0),
        low_battery=counts.get("low_battery", 0),
        reboots=counts.get("reboot", 0),
        efficiency_warnings=counts.get("rarely_used", 0) + counts.get("poor_power_saving", 0)
        + counts.get("excessive_continuous_on", 0),
    )

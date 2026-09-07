from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.anomalies import detect_period_anomalies
from app.analytics.energy import estimate_energy
from app.analytics.periods import resolve_window
from app.analytics.state_duration import compute_state_durations
from app.core.config import Settings
from app.models.device import Device
from app.schemas.analytics import DeviceAnalytics, FleetSummary
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

    for device in devices:
        analytics = await compute_device_analytics(session, device.device_id, period, start, end, settings)
        entry = {
            "device_id": device.device_id,
            "usage_percent": analytics.usage_percent,
            "power_saving_percent": analytics.power_saving_percent,
            "communication_gap_count": analytics.communication_gap_count,
            "is_active": is_device_active(device, settings, now),
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
        total_anomalies_recent=total_anomalies_recent,
        estimated_fleet_energy_kwh=total_energy if have_energy else None,
        period=period or "custom",
        window_start=window_start,
        window_end=window_end,
    )

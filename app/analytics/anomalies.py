"""Deterministic, rule-based anomaly detection.

Every threshold lives in app.core.config.Settings — nothing here is a magic
number. Detection is intentionally simple and explainable (no ML): each rule
is a single documented comparison against a configured threshold.
"""

from dataclasses import dataclass
from datetime import datetime

from app.analytics.state_duration import DurationResult
from app.core.config import Settings

RARELY_USED = "rarely_used"
EXCESSIVE_ON = "excessive_continuous_on"
POOR_POWER_SAVING = "poor_power_saving"
COMMUNICATION_GAP = "communication_gap"
LOW_BATTERY = "low_battery"
REBOOT = "reboot"
ABNORMAL_POWER = "abnormal_power"


@dataclass(slots=True)
class AnomalyFinding:
    anomaly_type: str
    detected_at: datetime
    event_time: datetime
    details: dict


def detect_period_anomalies(
    device_id: str,
    result: DurationResult,
    settings: Settings,
    now: datetime,
    period_end: datetime,
) -> list[AnomalyFinding]:
    """Anomalies derivable from an aggregated duration result over a period."""
    findings: list[AnomalyFinding] = []

    if result.classified_seconds > 0:
        if result.usage_percent is not None and result.usage_percent < settings.rarely_used_on_percent:
            findings.append(
                AnomalyFinding(
                    RARELY_USED,
                    now,
                    period_end,
                    {"usage_percent": round(result.usage_percent, 2), "device_id": device_id},
                )
            )
        if (
            result.power_saving_percent is not None
            and result.power_saving_percent < settings.poor_power_saving_percent
        ):
            findings.append(
                AnomalyFinding(
                    POOR_POWER_SAVING,
                    now,
                    period_end,
                    {
                        "power_saving_percent": round(result.power_saving_percent, 2),
                        "device_id": device_id,
                    },
                )
            )

    excessive_on_seconds = settings.excessive_on_hours * 3600
    if result.max_on_streak_seconds > excessive_on_seconds:
        findings.append(
            AnomalyFinding(
                EXCESSIVE_ON,
                now,
                period_end,
                {
                    "continuous_on_hours": round(result.max_on_streak_seconds / 3600, 2),
                    "device_id": device_id,
                },
            )
        )

    if result.gap_count > 0:
        findings.append(
            AnomalyFinding(
                COMMUNICATION_GAP,
                now,
                period_end,
                {
                    "gap_count": result.gap_count,
                    "total_gap_hours": round(result.gap_seconds / 3600, 2),
                    "device_id": device_id,
                },
            )
        )

    if result.reboot_count > 0:
        findings.append(
            AnomalyFinding(
                REBOOT,
                now,
                period_end,
                {"reboot_count": result.reboot_count, "device_id": device_id},
            )
        )

    return findings


def detect_low_battery(
    device_id: str, battery_percent: float, settings: Settings, event_time: datetime, now: datetime
) -> AnomalyFinding | None:
    if battery_percent < settings.low_battery_percent:
        return AnomalyFinding(
            LOW_BATTERY,
            now,
            event_time,
            {"battery_percent": battery_percent, "device_id": device_id},
        )
    return None


def detect_abnormal_power(
    device_id: str,
    power_watts: float,
    baseline_avg_watts: float,
    settings: Settings,
    event_time: datetime,
    now: datetime,
) -> AnomalyFinding | None:
    """Flags power draw far above a device's own historical baseline.

    Uses a simple explainable multiplier threshold rather than a statistical
    model — sufficient for a bounded, explainable anomaly rule per spec.
    """
    if baseline_avg_watts <= 0:
        return None
    if power_watts > baseline_avg_watts * settings.abnormal_power_multiplier:
        return AnomalyFinding(
            ABNORMAL_POWER,
            now,
            event_time,
            {
                "power_watts": power_watts,
                "baseline_avg_watts": round(baseline_avg_watts, 2),
                "device_id": device_id,
            },
        )
    return None

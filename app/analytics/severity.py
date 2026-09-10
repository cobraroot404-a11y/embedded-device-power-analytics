"""Maps an anomaly type (+ its details) to a display severity.

Deterministic and rule-based, matching the rest of the anomaly engine — no
ML, no hidden scoring.
"""

INFO = "INFO"
WARNING = "WARNING"
CRITICAL = "CRITICAL"

_DEFAULT_SEVERITY = {
    "reboot": INFO,
    "rarely_used": INFO,
    "poor_power_saving": WARNING,
    "excessive_continuous_on": WARNING,
    "communication_gap": WARNING,
    "low_battery": WARNING,
    "abnormal_power": WARNING,
}


def get_severity(anomaly_type: str, details: dict) -> str:
    if anomaly_type == "low_battery":
        battery = details.get("battery_percent")
        if isinstance(battery, int | float) and battery < 10:
            return CRITICAL
    if anomaly_type == "communication_gap":
        gap_hours = details.get("total_gap_hours") or (details.get("gap_seconds", 0) / 3600)
        if gap_hours and gap_hours > 6:
            return CRITICAL
    return _DEFAULT_SEVERITY.get(anomaly_type, WARNING)

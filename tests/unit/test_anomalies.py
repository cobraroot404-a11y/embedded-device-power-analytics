from datetime import UTC, datetime

from app.analytics.anomalies import (
    ABNORMAL_POWER,
    COMMUNICATION_GAP,
    EXCESSIVE_ON,
    LOW_BATTERY,
    POOR_POWER_SAVING,
    RARELY_USED,
    REBOOT,
    detect_abnormal_power,
    detect_low_battery,
    detect_period_anomalies,
)
from app.analytics.state_duration import DurationResult
from app.core.config import Settings

NOW = datetime(2026, 9, 6, 12, 0, tzinfo=UTC)
PERIOD_END = datetime(2026, 9, 7, 0, 0, tzinfo=UTC)


def _settings() -> Settings:
    return Settings(database_url="postgresql+asyncpg://u:p@localhost/db")


def test_rarely_used_flagged_below_threshold() -> None:
    result = DurationResult(on_seconds=100, sleep_seconds=4000, off_seconds=0)
    findings = detect_period_anomalies("MIF-001", result, _settings(), NOW, PERIOD_END)
    assert any(f.anomaly_type == RARELY_USED for f in findings)


def test_not_rarely_used_above_threshold() -> None:
    result = DurationResult(on_seconds=2000, sleep_seconds=2000, off_seconds=0)
    findings = detect_period_anomalies("MIF-001", result, _settings(), NOW, PERIOD_END)
    assert not any(f.anomaly_type == RARELY_USED for f in findings)


def test_poor_power_saving_flagged() -> None:
    result = DurationResult(on_seconds=9000, sleep_seconds=500, off_seconds=100)
    findings = detect_period_anomalies("MIF-001", result, _settings(), NOW, PERIOD_END)
    assert any(f.anomaly_type == POOR_POWER_SAVING for f in findings)


def test_excessive_continuous_on_flagged() -> None:
    result = DurationResult(on_seconds=9 * 3600, max_on_streak_seconds=9 * 3600)
    findings = detect_period_anomalies("MIF-001", result, _settings(), NOW, PERIOD_END)
    assert any(f.anomaly_type == EXCESSIVE_ON for f in findings)


def test_no_excessive_on_below_threshold() -> None:
    result = DurationResult(on_seconds=3600, max_on_streak_seconds=3600)
    findings = detect_period_anomalies("MIF-001", result, _settings(), NOW, PERIOD_END)
    assert not any(f.anomaly_type == EXCESSIVE_ON for f in findings)


def test_communication_gap_flagged_when_gaps_present() -> None:
    result = DurationResult(on_seconds=100, gap_count=2, gap_seconds=7200)
    findings = detect_period_anomalies("MIF-001", result, _settings(), NOW, PERIOD_END)
    assert any(f.anomaly_type == COMMUNICATION_GAP for f in findings)


def test_reboot_flagged_when_reboots_present() -> None:
    result = DurationResult(on_seconds=100, reboot_count=1)
    findings = detect_period_anomalies("MIF-001", result, _settings(), NOW, PERIOD_END)
    assert any(f.anomaly_type == REBOOT for f in findings)


def test_low_battery_detected() -> None:
    finding = detect_low_battery("MIF-001", 15.0, _settings(), NOW, NOW)
    assert finding is not None
    assert finding.anomaly_type == LOW_BATTERY


def test_battery_above_threshold_not_flagged() -> None:
    finding = detect_low_battery("MIF-001", 50.0, _settings(), NOW, NOW)
    assert finding is None


def test_abnormal_power_detected_above_multiplier() -> None:
    finding = detect_abnormal_power("MIF-001", 20.0, 5.0, _settings(), NOW, NOW)
    assert finding is not None
    assert finding.anomaly_type == ABNORMAL_POWER


def test_normal_power_not_flagged() -> None:
    finding = detect_abnormal_power("MIF-001", 5.5, 5.0, _settings(), NOW, NOW)
    assert finding is None


def test_zero_baseline_power_never_flagged() -> None:
    finding = detect_abnormal_power("MIF-001", 5.0, 0.0, _settings(), NOW, NOW)
    assert finding is None

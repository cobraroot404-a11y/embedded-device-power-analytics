from app.analytics.severity import CRITICAL, INFO, WARNING, get_severity


def test_reboot_is_info() -> None:
    assert get_severity("reboot", {}) == INFO


def test_low_battery_is_warning_above_ten_percent() -> None:
    assert get_severity("low_battery", {"battery_percent": 15}) == WARNING


def test_low_battery_is_critical_below_ten_percent() -> None:
    assert get_severity("low_battery", {"battery_percent": 5}) == CRITICAL


def test_communication_gap_is_warning_by_default() -> None:
    assert get_severity("communication_gap", {"total_gap_hours": 1}) == WARNING


def test_long_communication_gap_is_critical() -> None:
    assert get_severity("communication_gap", {"total_gap_hours": 10}) == CRITICAL


def test_unknown_anomaly_type_defaults_to_warning() -> None:
    assert get_severity("something_new", {}) == WARNING

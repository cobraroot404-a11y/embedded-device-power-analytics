from datetime import datetime

from pydantic import BaseModel


class DeviceOut(BaseModel):
    device_id: str
    first_seen: datetime
    last_seen: datetime
    last_state: str | None
    last_boot_id: str | None
    is_active: bool


class DeviceAnalytics(BaseModel):
    device_id: str
    period: str
    window_start: datetime
    window_end: datetime
    on_seconds: float
    sleep_seconds: float
    off_seconds: float
    unknown_seconds: float
    classified_seconds: float
    usage_percent: float | None
    power_saving_percent: float | None
    communication_gap_count: int
    communication_gap_seconds: float
    reboot_count: int
    on_avg_power_watts: float | None
    sleep_avg_power_watts: float | None
    off_avg_power_watts: float | None
    estimated_energy_kwh: float | None
    energy_note: str = (
        "Energy is an estimate derived from observed power_watts samples, not accumulated meter data."
    )


class AnomalyOut(BaseModel):
    id: str
    device_id: str
    anomaly_type: str
    detected_at: datetime
    event_time: datetime
    details: dict


class FleetSummary(BaseModel):
    total_devices: int
    active_devices: int
    average_usage_percent: float | None
    average_power_saving_percent: float | None
    highest_usage_devices: list[dict]
    lowest_usage_devices: list[dict]
    inefficient_devices: list[dict]
    devices_with_gaps: list[dict]
    total_anomalies_recent: int
    estimated_fleet_energy_kwh: float | None
    period: str
    window_start: datetime
    window_end: datetime

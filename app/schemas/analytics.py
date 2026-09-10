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
    severity: str
    detected_at: datetime
    event_time: datetime
    details: dict


class PagedAnomalies(BaseModel):
    items: list[AnomalyOut]
    total: int
    limit: int
    offset: int


class FleetSummary(BaseModel):
    total_devices: int
    active_devices: int
    average_usage_percent: float | None
    average_power_saving_percent: float | None
    highest_usage_devices: list[dict]
    lowest_usage_devices: list[dict]
    inefficient_devices: list[dict]
    devices_with_gaps: list[dict]
    all_devices: list[dict]
    total_anomalies_recent: int
    estimated_fleet_energy_kwh: float | None
    period: str
    window_start: datetime
    window_end: datetime


class TimelineSegmentOut(BaseModel):
    start: datetime
    end: datetime
    state: str
    reason: str | None


class DeviceTimeline(BaseModel):
    device_id: str
    window_start: datetime
    window_end: datetime
    segments: list[TimelineSegmentOut]
    reboots: list[datetime]


class FleetStates(BaseModel):
    on: int
    sleep: int
    off: int
    unknown: int
    total: int


class FleetHealthDistribution(BaseModel):
    healthy: int
    warning: int
    critical: int
    offline: int


class FleetUsageTrendPoint(BaseModel):
    bucket_start: datetime
    usage_percent: float | None
    power_saving_percent: float | None
    classified_seconds: float
    unknown_seconds: float


class FleetUsageTrend(BaseModel):
    period: str
    window_start: datetime
    window_end: datetime
    points: list[FleetUsageTrendPoint]


class DevicePowerSummary(BaseModel):
    device_id: str
    avg_power_watts: float | None
    estimated_energy_kwh: float | None
    battery_percent: float | None


class PowerTrendPoint(BaseModel):
    bucket_start: datetime
    avg_power_watts: float | None


class FleetPowerAnalytics(BaseModel):
    period: str
    window_start: datetime
    window_end: datetime
    devices: list[DevicePowerSummary]
    trend: list[PowerTrendPoint]
    estimated_fleet_energy_kwh: float | None


class TelemetryEventOut(BaseModel):
    id: str
    time: datetime
    device_id: str
    message_id: str
    state: str
    battery_percent: float | None
    power_watts: float | None
    boot_id: str | None
    ingested_at: datetime


class TelemetryPage(BaseModel):
    items: list[TelemetryEventOut]
    total: int
    limit: int
    offset: int


class TelemetryQuality(BaseModel):
    received: int
    accepted: int
    rejected: int
    duplicates: int
    out_of_order: int
    communication_gaps: int


class ServiceStatus(BaseModel):
    name: str
    status: str
    detail: str | None = None


class SystemHealth(BaseModel):
    checked_at: datetime
    services: list[ServiceStatus]


class FleetOverview(BaseModel):
    summary: FleetSummary
    states: FleetStates
    health: FleetHealthDistribution


class AnomalySummary(BaseModel):
    total_active: int
    communication_gaps: int
    power_warnings: int
    low_battery: int
    reboots: int
    efficiency_warnings: int

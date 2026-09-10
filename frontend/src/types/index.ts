export type DeviceState = "ON" | "SLEEP" | "OFF" | "UNKNOWN";

export interface Device {
  device_id: string;
  first_seen: string;
  last_seen: string;
  last_state: DeviceState | null;
  last_boot_id: string | null;
  is_active: boolean;
}

export interface DeviceAnalytics {
  device_id: string;
  period: string;
  window_start: string;
  window_end: string;
  on_seconds: number;
  sleep_seconds: number;
  off_seconds: number;
  unknown_seconds: number;
  classified_seconds: number;
  usage_percent: number | null;
  power_saving_percent: number | null;
  communication_gap_count: number;
  communication_gap_seconds: number;
  reboot_count: number;
  on_avg_power_watts: number | null;
  sleep_avg_power_watts: number | null;
  off_avg_power_watts: number | null;
  estimated_energy_kwh: number | null;
  energy_note: string;
}

export type Severity = "INFO" | "WARNING" | "CRITICAL";

export interface Anomaly {
  id: string;
  device_id: string;
  anomaly_type: string;
  severity: Severity;
  detected_at: string;
  event_time: string;
  details: Record<string, unknown>;
}

export interface PagedAnomalies {
  items: Anomaly[];
  total: number;
  limit: number;
  offset: number;
}

export interface AnomalySummary {
  total_active: number;
  communication_gaps: number;
  power_warnings: number;
  low_battery: number;
  reboots: number;
  efficiency_warnings: number;
}

export interface RankedDevice {
  device_id: string;
  usage_percent: number | null;
  power_saving_percent: number | null;
  communication_gap_count: number;
  is_active: boolean;
  estimated_energy_kwh: number | null;
  anomaly_count: number;
  on_seconds: number;
  sleep_seconds: number;
  off_seconds: number;
  unknown_seconds: number;
}

export interface FleetSummary {
  total_devices: number;
  active_devices: number;
  average_usage_percent: number | null;
  average_power_saving_percent: number | null;
  highest_usage_devices: RankedDevice[];
  lowest_usage_devices: RankedDevice[];
  inefficient_devices: RankedDevice[];
  devices_with_gaps: RankedDevice[];
  all_devices: RankedDevice[];
  total_anomalies_recent: number;
  estimated_fleet_energy_kwh: number | null;
  period: string;
  window_start: string;
  window_end: string;
}

export interface FleetStates {
  on: number;
  sleep: number;
  off: number;
  unknown: number;
  total: number;
}

export interface FleetHealthDistribution {
  healthy: number;
  warning: number;
  critical: number;
  offline: number;
}

export interface FleetOverview {
  summary: FleetSummary;
  states: FleetStates;
  health: FleetHealthDistribution;
}

export interface FleetUsageTrendPoint {
  bucket_start: string;
  usage_percent: number | null;
  power_saving_percent: number | null;
  classified_seconds: number;
  unknown_seconds: number;
}

export interface FleetUsageTrend {
  period: string;
  window_start: string;
  window_end: string;
  points: FleetUsageTrendPoint[];
}

export interface DevicePowerSummary {
  device_id: string;
  avg_power_watts: number | null;
  estimated_energy_kwh: number | null;
  battery_percent: number | null;
}

export interface PowerTrendPoint {
  bucket_start: string;
  avg_power_watts: number | null;
}

export interface FleetPowerAnalytics {
  period: string;
  window_start: string;
  window_end: string;
  devices: DevicePowerSummary[];
  trend: PowerTrendPoint[];
  estimated_fleet_energy_kwh: number | null;
}

export interface TelemetryEvent {
  id: string;
  time: string;
  device_id: string;
  message_id: string;
  state: DeviceState;
  battery_percent: number | null;
  power_watts: number | null;
  boot_id: string | null;
  ingested_at: string;
}

export interface TelemetryPage {
  items: TelemetryEvent[];
  total: number;
  limit: number;
  offset: number;
}

export interface TimelineSegment {
  start: string;
  end: string;
  state: DeviceState;
  reason: string | null;
}

export interface DeviceTimeline {
  device_id: string;
  window_start: string;
  window_end: string;
  segments: TimelineSegment[];
  reboots: string[];
}

export type ServiceStatusValue = "healthy" | "degraded" | "unavailable" | "unknown";

export interface ServiceStatus {
  name: string;
  status: ServiceStatusValue;
  detail: string | null;
}

export interface SystemHealth {
  checked_at: string;
  services: ServiceStatus[];
}

export type Period = "hourly" | "daily" | "weekly" | "monthly";

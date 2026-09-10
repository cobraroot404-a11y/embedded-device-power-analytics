import type { Anomaly, Device, DeviceAnalytics, DeviceTimeline, Period } from "../types";
import { apiGet } from "./client";

export function getDevices(): Promise<Device[]> {
  return apiGet<Device[]>("/devices");
}

export function getDevice(deviceId: string): Promise<Device> {
  return apiGet<Device>(`/devices/${deviceId}`);
}

export function getDeviceSummary(deviceId: string): Promise<DeviceAnalytics> {
  return apiGet<DeviceAnalytics>(`/devices/${deviceId}/summary`);
}

export function getDeviceAnalytics(deviceId: string, period: Period): Promise<DeviceAnalytics> {
  return apiGet<DeviceAnalytics>(`/devices/${deviceId}/analytics`, { period });
}

export function getDeviceAnomalies(deviceId: string, limit = 100): Promise<Anomaly[]> {
  return apiGet<Anomaly[]>(`/devices/${deviceId}/anomalies`, { limit });
}

export function getDeviceTimeline(deviceId: string, period: Period): Promise<DeviceTimeline> {
  return apiGet<DeviceTimeline>(`/devices/${deviceId}/timeline`, { period });
}

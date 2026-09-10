import type { DeviceState, ServiceStatusValue, Severity } from "../types";

export interface StatusStyle {
  label: string;
  dotClass: string;
  textClass: string;
}

export function deviceStateStyle(state: DeviceState | null): StatusStyle {
  switch (state) {
    case "ON":
      return { label: "ON", dotClass: "bg-status-healthy", textClass: "text-status-healthy" };
    case "SLEEP":
      return { label: "SLEEP", dotClass: "bg-accent-600", textClass: "text-accent-700" };
    case "OFF":
      return { label: "OFF", dotClass: "bg-ink-500", textClass: "text-ink-500" };
    default:
      return { label: "UNKNOWN", dotClass: "bg-status-warning", textClass: "text-status-warning" };
  }
}

export function serviceStatusStyle(status: ServiceStatusValue): StatusStyle {
  switch (status) {
    case "healthy":
      return { label: "Healthy", dotClass: "bg-status-healthy", textClass: "text-status-healthy" };
    case "degraded":
      return { label: "Degraded", dotClass: "bg-status-warning", textClass: "text-status-warning" };
    case "unavailable":
      return { label: "Unavailable", dotClass: "bg-status-critical", textClass: "text-status-critical" };
    default:
      return { label: "Unknown", dotClass: "bg-ink-500", textClass: "text-ink-500" };
  }
}

export function severityStyle(severity: Severity): StatusStyle {
  switch (severity) {
    case "CRITICAL":
      return { label: "Critical", dotClass: "bg-status-critical", textClass: "text-status-critical" };
    case "WARNING":
      return { label: "Warning", dotClass: "bg-status-warning", textClass: "text-status-warning" };
    default:
      return { label: "Info", dotClass: "bg-accent-600", textClass: "text-accent-700" };
  }
}

export function communicationStyle(isActive: boolean): StatusStyle {
  return isActive
    ? { label: "Online", dotClass: "bg-status-healthy", textClass: "text-status-healthy" }
    : { label: "Offline", dotClass: "bg-status-critical", textClass: "text-status-critical" };
}

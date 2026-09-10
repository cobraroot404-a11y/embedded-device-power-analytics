import type { TelemetryPage } from "../types";
import { apiGet } from "./client";

export interface TelemetryFilters {
  device_id?: string;
  state?: string;
  start?: string;
  end?: string;
  limit?: number;
  offset?: number;
}

export function getTelemetryPage(filters: TelemetryFilters = {}): Promise<TelemetryPage> {
  return apiGet<TelemetryPage>("/telemetry", { ...filters });
}

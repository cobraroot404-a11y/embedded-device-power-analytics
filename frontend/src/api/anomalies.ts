import type { AnomalySummary, PagedAnomalies } from "../types";
import { apiGet } from "./client";

export interface AnomalyFilters {
  device_id?: string;
  anomaly_type?: string;
  start?: string;
  end?: string;
  limit?: number;
  offset?: number;
}

export function getAnomalies(filters: AnomalyFilters = {}): Promise<PagedAnomalies> {
  return apiGet<PagedAnomalies>("/anomalies", { ...filters });
}

export function getAnomalySummary(hours = 24): Promise<AnomalySummary> {
  return apiGet<AnomalySummary>("/anomalies/summary", { hours });
}

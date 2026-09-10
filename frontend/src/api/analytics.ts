import type {
  FleetOverview,
  FleetPowerAnalytics,
  FleetStates,
  FleetSummary,
  FleetUsageTrend,
  Period,
} from "../types";
import { apiGet } from "./client";

export function getFleetSummary(period: Period): Promise<FleetSummary> {
  return apiGet<FleetSummary>("/fleet/summary", { period });
}

export function getFleetOverview(period: Period): Promise<FleetOverview> {
  return apiGet<FleetOverview>("/fleet/overview", { period });
}

export function getFleetStates(): Promise<FleetStates> {
  return apiGet<FleetStates>("/fleet/states");
}

export function getFleetUsageTrend(period: Period): Promise<FleetUsageTrend> {
  return apiGet<FleetUsageTrend>("/fleet/usage", { period });
}

export function getFleetPower(period: Period): Promise<FleetPowerAnalytics> {
  return apiGet<FleetPowerAnalytics>("/fleet/power", { period });
}

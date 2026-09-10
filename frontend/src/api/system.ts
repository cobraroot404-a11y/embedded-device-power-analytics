import type { SystemHealth } from "../types";
import { apiGet } from "./client";

export function getSystemHealth(): Promise<SystemHealth> {
  return apiGet<SystemHealth>("/system/health");
}

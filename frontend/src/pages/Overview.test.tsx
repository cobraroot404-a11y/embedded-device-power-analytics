import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { Overview } from "./Overview";

vi.mock("../api/analytics", () => ({
  getFleetOverview: vi.fn().mockResolvedValue({
    summary: {
      total_devices: 3,
      active_devices: 2,
      average_usage_percent: 64.7,
      average_power_saving_percent: 35.3,
      highest_usage_devices: [],
      lowest_usage_devices: [],
      inefficient_devices: [],
      devices_with_gaps: [],
      all_devices: [],
      total_anomalies_recent: 4,
      estimated_fleet_energy_kwh: 1.2,
      period: "daily",
      window_start: "2026-09-09T00:00:00Z",
      window_end: "2026-09-10T00:00:00Z",
    },
    states: { on: 1, sleep: 1, off: 0, unknown: 1, total: 3 },
    health: { healthy: 2, warning: 1, critical: 0, offline: 0 },
  }),
  getFleetUsageTrend: vi.fn().mockResolvedValue({ period: "daily", window_start: "", window_end: "", points: [] }),
  getFleetPower: vi.fn().mockResolvedValue({
    period: "daily",
    window_start: "",
    window_end: "",
    devices: [],
    trend: [],
    estimated_fleet_energy_kwh: null,
  }),
}));

describe("Overview", () => {
  it("renders fleet KPIs from real API data", async () => {
    render(
      <MemoryRouter>
        <Overview />
      </MemoryRouter>,
    );

    await waitFor(() => expect(screen.getByText("3")).toBeInTheDocument());
    expect(screen.getByText("64.7%")).toBeInTheDocument();
    expect(screen.getByText("35.3%")).toBeInTheDocument();
    expect(screen.getByText("4")).toBeInTheDocument();
  });

  it("shows an empty state when there is no attention-worthy device", async () => {
    render(
      <MemoryRouter>
        <Overview />
      </MemoryRouter>,
    );
    await waitFor(() =>
      expect(screen.getByText("No devices currently require attention.")).toBeInTheDocument(),
    );
  });
});

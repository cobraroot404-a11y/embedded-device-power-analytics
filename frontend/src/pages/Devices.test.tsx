import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { Devices } from "./Devices";

const { DEVICES } = vi.hoisted(() => ({
  DEVICES: [
    {
      device_id: "MIF-001",
      first_seen: "2026-09-01T00:00:00Z",
      last_seen: "2026-09-10T00:00:00Z",
      last_state: "ON",
      last_boot_id: "boot-a",
      is_active: true,
    },
    {
      device_id: "MIF-002",
      first_seen: "2026-09-01T00:00:00Z",
      last_seen: "2026-09-10T00:00:00Z",
      last_state: null,
      last_boot_id: null,
      is_active: false,
    },
  ],
}));

vi.mock("../api/devices", () => ({
  getDevices: vi.fn().mockResolvedValue(DEVICES),
}));

vi.mock("../api/analytics", () => ({
  getFleetSummary: vi.fn().mockResolvedValue({
    total_devices: 2,
    active_devices: 1,
    average_usage_percent: 50,
    average_power_saving_percent: 50,
    highest_usage_devices: [],
    lowest_usage_devices: [],
    inefficient_devices: [],
    devices_with_gaps: [],
    all_devices: [
      {
        device_id: "MIF-001",
        usage_percent: 80,
        power_saving_percent: 20,
        communication_gap_count: 0,
        is_active: true,
        estimated_energy_kwh: 1,
        anomaly_count: 0,
        on_seconds: 0,
        sleep_seconds: 0,
        off_seconds: 0,
        unknown_seconds: 0,
      },
    ],
    total_anomalies_recent: 0,
    estimated_fleet_energy_kwh: null,
    period: "daily",
    window_start: "",
    window_end: "",
  }),
}));

describe("Devices page", () => {
  it("renders the device table with unknown-state device shown correctly", async () => {
    render(
      <MemoryRouter>
        <Devices />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByText("MIF-001")).toBeInTheDocument());
    expect(screen.getByText("MIF-002")).toBeInTheDocument();
    // "UNKNOWN" also appears as a <select> option, so assert on the specific
    // status badge cell rather than a bare text match.
    const row = screen.getByText("MIF-002").closest("tr");
    expect(row).not.toBeNull();
    expect(row!.querySelector("td:nth-child(3)")?.textContent).toBe("UNKNOWN");
  });

  it("filters the table by search term", async () => {
    render(
      <MemoryRouter>
        <Devices />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByText("MIF-001")).toBeInTheDocument());

    const search = screen.getByLabelText("Search devices");
    await userEvent.type(search, "MIF-002");

    expect(screen.queryByText("MIF-001")).not.toBeInTheDocument();
    expect(screen.getByText("MIF-002")).toBeInTheDocument();
  });

  it("links each device row to its detail page", async () => {
    render(
      <MemoryRouter>
        <Devices />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByText("MIF-001")).toBeInTheDocument());
    const link = screen.getByRole("link", { name: "MIF-001" });
    expect(link).toHaveAttribute("href", "/devices/MIF-001");
  });
});

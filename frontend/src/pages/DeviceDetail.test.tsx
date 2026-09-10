import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { DeviceDetail } from "./DeviceDetail";

vi.mock("../api/devices", () => ({
  getDevice: vi.fn().mockResolvedValue({
    device_id: "MIF-007",
    first_seen: "2026-09-01T00:00:00Z",
    last_seen: "2026-09-10T00:00:00Z",
    last_state: "ON",
    last_boot_id: "boot-x",
    is_active: true,
  }),
  getDeviceAnalytics: vi.fn().mockResolvedValue({
    device_id: "MIF-007",
    period: "daily",
    window_start: "",
    window_end: "",
    on_seconds: 3600,
    sleep_seconds: 0,
    off_seconds: 0,
    unknown_seconds: 0,
    classified_seconds: 3600,
    usage_percent: 100,
    power_saving_percent: 0,
    communication_gap_count: 0,
    communication_gap_seconds: 0,
    reboot_count: 0,
    on_avg_power_watts: null,
    sleep_avg_power_watts: null,
    off_avg_power_watts: null,
    estimated_energy_kwh: null,
    energy_note: "",
  }),
  getDeviceAnomalies: vi.fn().mockResolvedValue([]),
  getDeviceTimeline: vi.fn().mockResolvedValue({
    device_id: "MIF-007",
    window_start: "2026-09-10T00:00:00Z",
    window_end: "2026-09-10T01:00:00Z",
    segments: [],
    reboots: [],
  }),
}));

vi.mock("../api/telemetry", () => ({
  getTelemetryPage: vi.fn().mockResolvedValue({ items: [], total: 0, limit: 200, offset: 0 }),
}));

describe("DeviceDetail page", () => {
  it("renders the device header for the routed device ID", async () => {
    render(
      <MemoryRouter initialEntries={["/devices/MIF-007"]}>
        <Routes>
          <Route path="/devices/:deviceId" element={<DeviceDetail />} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => expect(screen.getByText("MIF-007")).toBeInTheDocument());
    expect(screen.getByText("No telemetry available for this reporting period.")).toBeInTheDocument();
    expect(screen.getByText("No anomalies detected.")).toBeInTheDocument();
  });
});

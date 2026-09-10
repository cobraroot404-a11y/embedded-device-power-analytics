import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { Anomalies } from "./Anomalies";

vi.mock("../api/anomalies", () => ({
  getAnomalySummary: vi.fn().mockResolvedValue({
    total_active: 1,
    communication_gaps: 1,
    power_warnings: 0,
    low_battery: 0,
    reboots: 0,
    efficiency_warnings: 0,
  }),
  getAnomalies: vi.fn().mockResolvedValue({
    items: [
      {
        id: "1",
        device_id: "MIF-005",
        anomaly_type: "communication_gap",
        severity: "WARNING",
        detected_at: "2026-09-10T00:00:00Z",
        event_time: "2026-09-10T00:00:00Z",
        details: {},
      },
    ],
    total: 1,
    limit: 20,
    offset: 0,
  }),
}));

describe("Anomalies page with data", () => {
  it("renders a detected anomaly row", async () => {
    render(
      <MemoryRouter>
        <Anomalies />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByText("MIF-005")).toBeInTheDocument());
    expect(screen.getByText("communication_gap")).toBeInTheDocument();
    expect(screen.getByText("Warning")).toBeInTheDocument();
  });
});

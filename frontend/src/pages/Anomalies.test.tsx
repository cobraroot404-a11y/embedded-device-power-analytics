import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { Anomalies } from "./Anomalies";

vi.mock("../api/anomalies", () => ({
  getAnomalySummary: vi.fn().mockResolvedValue({
    total_active: 0,
    communication_gaps: 0,
    power_warnings: 0,
    low_battery: 0,
    reboots: 0,
    efficiency_warnings: 0,
  }),
  getAnomalies: vi.fn().mockResolvedValue({ items: [], total: 0, limit: 20, offset: 0 }),
}));

describe("Anomalies page", () => {
  it("shows an empty state when there are no anomalies", async () => {
    render(
      <MemoryRouter>
        <Anomalies />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByText("No anomalies detected.")).toBeInTheDocument());
  });
});

import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { Overview } from "./Overview";

vi.mock("../api/analytics", () => ({
  getFleetOverview: vi.fn().mockRejectedValue(new Error("network down")),
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

describe("Overview error state", () => {
  it("shows a retry-capable error message when the API call fails", async () => {
    render(
      <MemoryRouter>
        <Overview />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByText("Unable to load fleet analytics.")).toBeInTheDocument());
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
  });
});

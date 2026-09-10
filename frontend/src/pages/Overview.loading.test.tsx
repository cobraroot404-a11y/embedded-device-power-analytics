import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { Overview } from "./Overview";

vi.mock("../api/analytics", () => ({
  getFleetOverview: vi.fn(() => new Promise(() => {})),
  getFleetUsageTrend: vi.fn(() => new Promise(() => {})),
  getFleetPower: vi.fn(() => new Promise(() => {})),
}));

describe("Overview loading state", () => {
  it("shows skeleton KPI cards while the initial request is in flight", () => {
    render(
      <MemoryRouter>
        <Overview />
      </MemoryRouter>,
    );
    expect(screen.getByText("Fleet Overview")).toBeInTheDocument();
    expect(document.querySelectorAll(".animate-pulse").length).toBeGreaterThan(0);
  });
});

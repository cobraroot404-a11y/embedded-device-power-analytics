import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { PeriodSelector } from "./PeriodSelector";

describe("PeriodSelector", () => {
  it("calls onChange with the selected period", async () => {
    const onChange = vi.fn();
    render(<PeriodSelector value="daily" onChange={onChange} />);

    await userEvent.click(screen.getByRole("button", { name: "7D" }));

    expect(onChange).toHaveBeenCalledWith("weekly");
  });

  it("marks the active period as pressed", () => {
    render(<PeriodSelector value="monthly" onChange={vi.fn()} />);
    expect(screen.getByRole("button", { name: "30D" })).toHaveAttribute("aria-pressed", "true");
  });
});

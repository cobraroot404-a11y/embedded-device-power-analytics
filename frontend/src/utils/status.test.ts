import { describe, expect, it } from "vitest";

import { deviceStateStyle, serviceStatusStyle, severityStyle } from "./status";

describe("deviceStateStyle", () => {
  it("renders a distinct style for the UNKNOWN state, not treated as ON", () => {
    const unknown = deviceStateStyle(null);
    const on = deviceStateStyle("ON");
    expect(unknown.label).toBe("UNKNOWN");
    expect(unknown.dotClass).not.toBe(on.dotClass);
  });
});

describe("serviceStatusStyle", () => {
  it("never fabricates a healthy status for an unknown service state", () => {
    const style = serviceStatusStyle("unknown");
    expect(style.label).toBe("Unknown");
  });
});

describe("severityStyle", () => {
  it("maps CRITICAL to the critical style", () => {
    expect(severityStyle("CRITICAL").label).toBe("Critical");
  });
});

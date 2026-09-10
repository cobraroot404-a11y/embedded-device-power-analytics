import { useEffect, useState } from "react";
import { NavLink, Outlet } from "react-router-dom";

import { getSystemHealth } from "../api/system";
import { formatUtcTimestamp } from "../utils/format";

const NAV_ITEMS = [
  { to: "/", label: "Overview", end: true },
  { to: "/devices", label: "Devices" },
  { to: "/analytics/usage", label: "Usage Analytics" },
  { to: "/analytics/power", label: "Power Analytics" },
  { to: "/anomalies", label: "Anomalies" },
  { to: "/telemetry", label: "Telemetry" },
  { to: "/system", label: "System Health" },
];

export function AppLayout() {
  const [platformHealthy, setPlatformHealthy] = useState<boolean | null>(null);
  const [now, setNow] = useState(new Date());

  useEffect(() => {
    let cancelled = false;
    getSystemHealth()
      .then((health) => {
        if (cancelled) return;
        setPlatformHealthy(health.services.every((s) => s.status === "healthy"));
      })
      .catch(() => setPlatformHealthy(null));
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const interval = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex min-h-screen flex-col">
      <header className="flex items-center justify-between border-b border-surface-200 bg-white px-6 py-3">
        <div className="flex items-center gap-3">
          <span className="text-lg font-semibold text-ink-900">MIF Analytics</span>
          <span className="text-sm text-ink-500">Embedded Device Power Analytics</span>
        </div>
        <div className="flex items-center gap-4 text-sm text-ink-500">
          <span className="flex items-center gap-1.5">
            <span
              className={`h-2 w-2 rounded-full ${
                platformHealthy === null
                  ? "bg-ink-500"
                  : platformHealthy
                    ? "bg-status-healthy"
                    : "bg-status-warning"
              }`}
            />
            {platformHealthy === null
              ? "Checking..."
              : platformHealthy
                ? "System Healthy"
                : "Attention Needed"}
          </span>
          <span>Last updated: {formatUtcTimestamp(now.toISOString())}</span>
        </div>
      </header>
      <div className="flex flex-1">
        <nav className="hidden w-56 shrink-0 border-r border-surface-200 bg-white p-3 md:block">
          <ul className="space-y-1">
            {NAV_ITEMS.map((item) => (
              <li key={item.to}>
                <NavLink
                  to={item.to}
                  end={item.end}
                  className={({ isActive }) =>
                    `block rounded px-3 py-2 text-sm font-medium ${
                      isActive ? "bg-ink-900 text-white" : "text-ink-700 hover:bg-surface-100"
                    }`
                  }
                >
                  {item.label}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
        <main className="flex-1 overflow-x-hidden p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

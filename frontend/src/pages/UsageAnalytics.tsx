import { useState } from "react";
import { Link } from "react-router-dom";

import { getFleetSummary, getFleetUsageTrend } from "../api/analytics";
import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { PeriodSelector } from "../components/PeriodSelector";
import { FleetUsageTrendChart } from "../charts/FleetUsageTrendChart";
import { StateDurationStackedBar } from "../charts/StateDurationStackedBar";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useApiData } from "../hooks/useApiData";
import type { Period } from "../types";
import { formatPercent } from "../utils/format";

export function UsageAnalytics() {
  const [period, setPeriod] = useState<Period>("daily");
  const summaryQuery = useApiData(() => getFleetSummary(period), [period]);
  const trendQuery = useApiData(() => getFleetUsageTrend(period), [period]);

  if (summaryQuery.error) {
    return <ErrorState message="Unable to load usage analytics." onRetry={summaryQuery.refetch} />;
  }

  const devices = summaryQuery.data?.all_devices ?? [];
  const usageBarData = devices
    .filter((d) => d.usage_percent !== null)
    .map((d) => ({ device_id: d.device_id, usage: Number(d.usage_percent?.toFixed(1)) }))
    .sort((a, b) => b.usage - a.usage);

  const underutilised = summaryQuery.data?.inefficient_devices ?? [];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-xl font-semibold text-ink-900">Usage Analytics</h1>
        <PeriodSelector value={period} onChange={setPeriod} />
      </div>

      <section className="rounded-md border border-surface-200 bg-white p-4">
        <h2 className="mb-2 text-sm font-medium text-ink-700">Usage by Device</h2>
        {usageBarData.length === 0 ? (
          <EmptyState message="No telemetry available for this reporting period." />
        ) : (
          <ResponsiveContainer width="100%" height={Math.max(220, usageBarData.length * 26)}>
            <BarChart data={usageBarData} layout="vertical" margin={{ top: 8, right: 24, bottom: 0, left: 8 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} />
              <XAxis type="number" domain={[0, 100]} unit="%" tick={{ fontSize: 11 }} />
              <YAxis type="category" dataKey="device_id" tick={{ fontSize: 11 }} width={70} />
              <Tooltip formatter={(value: number) => [`${value}%`, "Usage"]} />
              <Bar dataKey="usage" fill="#16a34a" radius={[0, 3, 3, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </section>

      <section className="rounded-md border border-surface-200 bg-white p-4">
        <h2 className="mb-2 text-sm font-medium text-ink-700">State Breakdown by Device</h2>
        {devices.length === 0 ? (
          <EmptyState message="No devices registered yet." />
        ) : (
          <StateDurationStackedBar rows={devices} />
        )}
      </section>

      <section className="rounded-md border border-surface-200 bg-white p-4">
        <h2 className="mb-2 text-sm font-medium text-ink-700">Daily Usage Trend</h2>
        {trendQuery.data && trendQuery.data.points.length > 0 ? (
          <FleetUsageTrendChart trend={trendQuery.data} />
        ) : (
          <EmptyState message="No telemetry available for this reporting period." />
        )}
      </section>

      <section className="rounded-md border border-surface-200 bg-white p-4">
        <h2 className="mb-2 text-sm font-medium text-ink-700">Underutilised Devices</h2>
        {underutilised.length === 0 ? (
          <EmptyState message="No underutilised devices detected." />
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="border-b border-surface-200 text-ink-500">
              <tr>
                <th className="px-2 py-2 font-medium">Device</th>
                <th className="px-2 py-2 font-medium">Usage %</th>
                <th className="px-2 py-2 font-medium">Power-Saving %</th>
              </tr>
            </thead>
            <tbody>
              {underutilised.map((d) => (
                <tr key={d.device_id} className="border-b border-surface-100 last:border-0">
                  <td className="px-2 py-2">
                    <Link to={`/devices/${d.device_id}`} className="text-accent-700 hover:underline">
                      {d.device_id}
                    </Link>
                  </td>
                  <td className="px-2 py-2">{formatPercent(d.usage_percent)}</td>
                  <td className="px-2 py-2">{formatPercent(d.power_saving_percent)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}

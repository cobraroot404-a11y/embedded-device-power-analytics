import { useState } from "react";
import { Link } from "react-router-dom";

import { getAnomalies } from "../api/anomalies";
import { getFleetPower, getFleetSummary } from "../api/analytics";
import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { PeriodSelector } from "../components/PeriodSelector";
import { EnergyBarChart } from "../charts/EnergyBarChart";
import { PowerTrendChart } from "../charts/PowerTrendChart";
import { useApiData } from "../hooks/useApiData";
import type { Period } from "../types";
import { formatPercent, formatRelativeTime, formatWatts } from "../utils/format";

export function PowerAnalytics() {
  const [period, setPeriod] = useState<Period>("daily");
  const powerQuery = useApiData(() => getFleetPower(period), [period]);
  const summaryQuery = useApiData(() => getFleetSummary(period), [period]);
  const abnormalQuery = useApiData(() => getAnomalies({ anomaly_type: "abnormal_power", limit: 20 }), []);

  if (powerQuery.error) {
    return <ErrorState message="Unable to load power analytics." onRetry={powerQuery.refetch} />;
  }

  const devicesByPower = [...(powerQuery.data?.devices ?? [])]
    .filter((d) => d.avg_power_watts !== null)
    .sort((a, b) => (b.avg_power_watts ?? 0) - (a.avg_power_watts ?? 0));

  const savingRanking = [...(summaryQuery.data?.all_devices ?? [])]
    .filter((d) => d.power_saving_percent !== null)
    .sort((a, b) => (b.power_saving_percent ?? 0) - (a.power_saving_percent ?? 0));

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-xl font-semibold text-ink-900">Power Analytics</h1>
        <PeriodSelector value={period} onChange={setPeriod} />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <section className="rounded-md border border-surface-200 bg-white p-4">
          <h2 className="mb-2 text-sm font-medium text-ink-700">Estimated Energy by Device</h2>
          {powerQuery.data && powerQuery.data.devices.length > 0 ? (
            <EnergyBarChart devices={powerQuery.data.devices} />
          ) : (
            <EmptyState message="No power telemetry available." />
          )}
        </section>
        <section className="rounded-md border border-surface-200 bg-white p-4">
          <h2 className="mb-2 text-sm font-medium text-ink-700">Fleet Power Trend</h2>
          {powerQuery.data && powerQuery.data.trend.length > 0 ? (
            <PowerTrendChart points={powerQuery.data.trend} />
          ) : (
            <EmptyState message="No power telemetry available." />
          )}
        </section>
      </div>

      <section className="rounded-md border border-surface-200 bg-white p-4">
        <h2 className="mb-2 text-sm font-medium text-ink-700">Average Power by Device</h2>
        {devicesByPower.length === 0 ? (
          <EmptyState message="No power telemetry available." />
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="border-b border-surface-200 text-ink-500">
              <tr>
                <th className="px-2 py-2 font-medium">Device</th>
                <th className="px-2 py-2 font-medium">Avg Power</th>
              </tr>
            </thead>
            <tbody>
              {devicesByPower.map((d) => (
                <tr key={d.device_id} className="border-b border-surface-100 last:border-0">
                  <td className="px-2 py-2">
                    <Link to={`/devices/${d.device_id}`} className="text-accent-700 hover:underline">
                      {d.device_id}
                    </Link>
                  </td>
                  <td className="px-2 py-2">{formatWatts(d.avg_power_watts)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <section className="rounded-md border border-surface-200 bg-white p-4">
          <h2 className="mb-2 text-sm font-medium text-ink-700">Power-Saving Ranking</h2>
          {savingRanking.length === 0 ? (
            <EmptyState message="No devices registered yet." />
          ) : (
            <ol className="space-y-1 text-sm">
              {savingRanking.map((d) => (
                <li key={d.device_id} className="flex justify-between border-b border-surface-100 py-1 last:border-0">
                  <Link to={`/devices/${d.device_id}`} className="text-accent-700 hover:underline">
                    {d.device_id}
                  </Link>
                  <span>{formatPercent(d.power_saving_percent)}</span>
                </li>
              ))}
            </ol>
          )}
        </section>
        <section className="rounded-md border border-surface-200 bg-white p-4">
          <h2 className="mb-2 text-sm font-medium text-ink-700">Abnormal Power Events</h2>
          {!abnormalQuery.data || abnormalQuery.data.items.length === 0 ? (
            <EmptyState message="No abnormal power events detected." />
          ) : (
            <ul className="divide-y divide-surface-200 text-sm">
              {abnormalQuery.data.items.map((a) => (
                <li key={a.id} className="flex justify-between py-2">
                  <Link to={`/devices/${a.device_id}`} className="text-accent-700 hover:underline">
                    {a.device_id}
                  </Link>
                  <span className="text-ink-500">{formatRelativeTime(a.event_time)}</span>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  );
}

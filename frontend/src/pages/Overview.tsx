import { useState } from "react";
import { Link } from "react-router-dom";

import { getFleetOverview, getFleetPower, getFleetUsageTrend } from "../api/analytics";
import { AutoRefreshSelector } from "../components/AutoRefreshSelector";
import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { KpiCard, KpiCardSkeleton } from "../components/KpiCard";
import { PeriodSelector } from "../components/PeriodSelector";
import { EfficiencyMatrixScatter } from "../charts/EfficiencyMatrixScatter";
import { EnergyBarChart } from "../charts/EnergyBarChart";
import { FleetHealthDonut } from "../charts/FleetHealthDonut";
import { FleetUsageTrendChart } from "../charts/FleetUsageTrendChart";
import { StateDistributionDonut } from "../charts/StateDistributionDonut";
import { useApiData } from "../hooks/useApiData";
import type { Period } from "../types";
import { formatEnergy, formatPercent } from "../utils/format";

export function Overview() {
  const [period, setPeriod] = useState<Period>("daily");
  const [refreshMs, setRefreshMs] = useState(30_000);

  const overview = useApiData(() => getFleetOverview(period), [period], refreshMs || null);
  const trend = useApiData(() => getFleetUsageTrend(period), [period], refreshMs || null);
  const power = useApiData(() => getFleetPower(period), [period], refreshMs || null);

  const loading = overview.loading && !overview.data;

  if (overview.error) {
    return <ErrorState message="Unable to load fleet analytics." onRetry={overview.refetch} />;
  }

  const summary = overview.data?.summary;
  const attention = summary
    ? [...summary.inefficient_devices, ...summary.devices_with_gaps].filter(
        (d, idx, arr) => arr.findIndex((x) => x.device_id === d.device_id) === idx,
      )
    : [];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-xl font-semibold text-ink-900">Fleet Overview</h1>
        <div className="flex items-center gap-3">
          <PeriodSelector value={period} onChange={setPeriod} />
          <AutoRefreshSelector value={refreshMs} onChange={setRefreshMs} />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
        {loading ? (
          Array.from({ length: 6 }).map((_, i) => <KpiCardSkeleton key={i} />)
        ) : (
          <>
            <KpiCard label="Total Devices" value={String(summary?.total_devices ?? 0)} />
            <KpiCard label="Active Devices" value={String(summary?.active_devices ?? 0)} />
            <KpiCard label="Fleet Usage" value={formatPercent(summary?.average_usage_percent)} />
            <KpiCard label="Power-Saving" value={formatPercent(summary?.average_power_saving_percent)} />
            <KpiCard label="Estimated Energy" value={formatEnergy(summary?.estimated_fleet_energy_kwh)} />
            <KpiCard label="Active Anomalies" value={String(summary?.total_anomalies_recent ?? 0)} />
          </>
        )}
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <section className="rounded-md border border-surface-200 bg-white p-4">
          <h2 className="mb-2 text-sm font-medium text-ink-700">State Distribution</h2>
          {overview.data ? (
            <StateDistributionDonut states={overview.data.states} />
          ) : (
            <EmptyState message="No devices registered yet." />
          )}
        </section>
        <section className="rounded-md border border-surface-200 bg-white p-4">
          <h2 className="mb-2 text-sm font-medium text-ink-700">Fleet Usage Trend</h2>
          {trend.data && trend.data.points.length > 0 ? (
            <FleetUsageTrendChart trend={trend.data} />
          ) : (
            <EmptyState message="No telemetry available for this reporting period." />
          )}
        </section>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <section className="rounded-md border border-surface-200 bg-white p-4">
          <h2 className="mb-2 text-sm font-medium text-ink-700">Energy by Device</h2>
          {power.data && power.data.devices.some((d) => d.estimated_energy_kwh !== null) ? (
            <EnergyBarChart devices={power.data.devices} />
          ) : (
            <EmptyState message="No power telemetry available." />
          )}
        </section>
        <section className="rounded-md border border-surface-200 bg-white p-4">
          <h2 className="mb-2 text-sm font-medium text-ink-700">Fleet Health</h2>
          {overview.data ? (
            <FleetHealthDonut health={overview.data.health} />
          ) : (
            <EmptyState message="No health data available." />
          )}
        </section>
      </div>

      <section className="rounded-md border border-surface-200 bg-white p-4">
        <h2 className="mb-2 text-sm font-medium text-ink-700">Device Efficiency Matrix</h2>
        {summary && summary.all_devices.length > 0 ? (
          <EfficiencyMatrixScatter devices={summary.all_devices} />
        ) : (
          <EmptyState message="No device analytics available yet." />
        )}
      </section>

      <section className="rounded-md border border-surface-200 bg-white p-4">
        <h2 className="mb-2 text-sm font-medium text-ink-700">Devices Requiring Attention</h2>
        {attention.length === 0 ? (
          <EmptyState message="No devices currently require attention." />
        ) : (
          <ul className="divide-y divide-surface-200">
            {attention.map((d) => (
              <li key={d.device_id} className="flex items-center justify-between py-2 text-sm">
                <Link to={`/devices/${d.device_id}`} className="font-medium text-accent-700 hover:underline">
                  {d.device_id}
                </Link>
                <span className="text-ink-500">
                  Usage {formatPercent(d.usage_percent)} · Gaps {d.communication_gap_count}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

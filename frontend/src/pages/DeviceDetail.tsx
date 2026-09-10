import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import { getDevice, getDeviceAnalytics, getDeviceAnomalies, getDeviceTimeline } from "../api/devices";
import { getTelemetryPage } from "../api/telemetry";
import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { KpiCard, KpiCardSkeleton } from "../components/KpiCard";
import { PeriodSelector } from "../components/PeriodSelector";
import { BatteryTrendChart } from "../charts/BatteryTrendChart";
import { DeviceTimelineChart } from "../charts/DeviceTimelineChart";
import { PowerTrendChart } from "../charts/PowerTrendChart";
import { useApiData } from "../hooks/useApiData";
import type { Period } from "../types";
import { formatDuration, formatEnergy, formatPercent, formatRelativeTime } from "../utils/format";
import { communicationStyle, deviceStateStyle, severityStyle } from "../utils/status";

export function DeviceDetail() {
  const { deviceId } = useParams<{ deviceId: string }>();
  const [period, setPeriod] = useState<Period>("daily");

  const deviceQuery = useApiData(() => getDevice(deviceId as string), [deviceId]);
  const analyticsQuery = useApiData(() => getDeviceAnalytics(deviceId as string, period), [deviceId, period]);
  const timelineQuery = useApiData(() => getDeviceTimeline(deviceId as string, period), [deviceId, period]);
  const anomaliesQuery = useApiData(() => getDeviceAnomalies(deviceId as string), [deviceId]);
  const telemetryQuery = useApiData(
    () => getTelemetryPage({ device_id: deviceId, limit: 200 }),
    [deviceId],
  );

  if (deviceQuery.error) {
    return <ErrorState message={`Unable to load device ${deviceId}.`} onRetry={deviceQuery.refetch} />;
  }

  const device = deviceQuery.data;
  const analytics = analyticsQuery.data;

  return (
    <div className="space-y-6">
      <div>
        <Link to="/devices" className="text-sm text-accent-700 hover:underline">
          &larr; Back to Devices
        </Link>
      </div>

      {deviceQuery.loading || !device ? (
        <div className="h-16 animate-pulse rounded bg-surface-200" />
      ) : (
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-xl font-semibold text-ink-900">{device.device_id}</h1>
            <p className="text-sm text-ink-500">
              Status: <span className={communicationStyle(device.is_active).textClass}>{communicationStyle(device.is_active).label}</span>
              {" · "}
              Current State: <span className={deviceStateStyle(device.last_state).textClass}>{deviceStateStyle(device.last_state).label}</span>
              {" · "}
              Last Seen: {formatRelativeTime(device.last_seen)}
              {" · "}
              Boot ID: {device.last_boot_id ?? "—"}
            </p>
          </div>
          <PeriodSelector value={period} onChange={setPeriod} />
        </div>
      )}

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4 lg:grid-cols-6">
        {analyticsQuery.loading || !analytics ? (
          Array.from({ length: 6 }).map((_, i) => <KpiCardSkeleton key={i} />)
        ) : (
          <>
            <KpiCard label="Usage %" value={formatPercent(analytics.usage_percent)} />
            <KpiCard label="Power-Saving %" value={formatPercent(analytics.power_saving_percent)} />
            <KpiCard label="ON Duration" value={formatDuration(analytics.on_seconds)} />
            <KpiCard label="SLEEP Duration" value={formatDuration(analytics.sleep_seconds)} />
            <KpiCard label="OFF Duration" value={formatDuration(analytics.off_seconds)} />
            <KpiCard label="Estimated Energy" value={formatEnergy(analytics.estimated_energy_kwh)} />
          </>
        )}
      </div>

      <section className="rounded-md border border-surface-200 bg-white p-4">
        <h2 className="mb-3 text-sm font-medium text-ink-700">State Timeline</h2>
        {timelineQuery.data ? (
          <DeviceTimelineChart timeline={timelineQuery.data} />
        ) : (
          <EmptyState message="No telemetry available for this reporting period." />
        )}
      </section>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <section className="rounded-md border border-surface-200 bg-white p-4">
          <h2 className="mb-2 text-sm font-medium text-ink-700">Power Trend</h2>
          {telemetryQuery.data && telemetryQuery.data.items.some((e) => e.power_watts !== null) ? (
            <PowerTrendChart
              points={telemetryQuery.data.items
                .filter((e) => e.power_watts !== null)
                .map((e) => ({ bucket_start: e.time, avg_power_watts: e.power_watts }))}
            />
          ) : (
            <EmptyState message="No power telemetry available." />
          )}
        </section>
        <section className="rounded-md border border-surface-200 bg-white p-4">
          <h2 className="mb-2 text-sm font-medium text-ink-700">Battery Trend</h2>
          {telemetryQuery.data && telemetryQuery.data.items.some((e) => e.battery_percent !== null) ? (
            <BatteryTrendChart events={telemetryQuery.data.items} />
          ) : (
            <EmptyState message="No battery telemetry available." />
          )}
        </section>
      </div>

      <section className="rounded-md border border-surface-200 bg-white p-4">
        <h2 className="mb-2 text-sm font-medium text-ink-700">Anomalies</h2>
        {!anomaliesQuery.data || anomaliesQuery.data.length === 0 ? (
          <EmptyState message="No anomalies detected." />
        ) : (
          <ul className="divide-y divide-surface-200">
            {anomaliesQuery.data.map((a) => (
              <li key={a.id} className="flex items-center justify-between py-2 text-sm">
                <span className={severityStyle(a.severity).textClass}>{a.anomaly_type}</span>
                <span className="text-ink-500">{formatRelativeTime(a.event_time)}</span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

import { useState } from "react";
import { Link } from "react-router-dom";

import { getAnomalies, getAnomalySummary } from "../api/anomalies";
import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { KpiCard, KpiCardSkeleton } from "../components/KpiCard";
import { TableSkeleton } from "../components/TableSkeleton";
import { useApiData } from "../hooks/useApiData";
import { formatUtcTimestamp } from "../utils/format";
import { severityStyle } from "../utils/status";

export function Anomalies() {
  const [deviceId, setDeviceId] = useState("");
  const [anomalyType, setAnomalyType] = useState("");
  const [page, setPage] = useState(0);
  const pageSize = 20;

  const summaryQuery = useApiData(() => getAnomalySummary(24), []);
  const listQuery = useApiData(
    () =>
      getAnomalies({
        device_id: deviceId || undefined,
        anomaly_type: anomalyType || undefined,
        limit: pageSize,
        offset: page * pageSize,
      }),
    [deviceId, anomalyType, page],
  );

  if (listQuery.error) {
    return <ErrorState message="Unable to load anomalies." onRetry={listQuery.refetch} />;
  }

  const totalPages = listQuery.data ? Math.max(1, Math.ceil(listQuery.data.total / pageSize)) : 1;

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-ink-900">Anomalies</h1>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
        {summaryQuery.loading || !summaryQuery.data ? (
          Array.from({ length: 6 }).map((_, i) => <KpiCardSkeleton key={i} />)
        ) : (
          <>
            <KpiCard label="Total Active" value={String(summaryQuery.data.total_active)} />
            <KpiCard label="Communication Gaps" value={String(summaryQuery.data.communication_gaps)} />
            <KpiCard label="Power Warnings" value={String(summaryQuery.data.power_warnings)} />
            <KpiCard label="Low Battery" value={String(summaryQuery.data.low_battery)} />
            <KpiCard label="Reboots" value={String(summaryQuery.data.reboots)} />
            <KpiCard label="Efficiency Warnings" value={String(summaryQuery.data.efficiency_warnings)} />
          </>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <input
          type="search"
          placeholder="Filter by device ID"
          aria-label="Filter by device"
          value={deviceId}
          onChange={(e) => {
            setDeviceId(e.target.value);
            setPage(0);
          }}
          className="rounded border border-surface-200 px-3 py-1.5 text-sm"
        />
        <select
          aria-label="Filter by type"
          value={anomalyType}
          onChange={(e) => {
            setAnomalyType(e.target.value);
            setPage(0);
          }}
          className="rounded border border-surface-200 px-2 py-1.5 text-sm"
        >
          <option value="">All types</option>
          <option value="communication_gap">Communication Gap</option>
          <option value="low_battery">Low Battery</option>
          <option value="reboot">Reboot</option>
          <option value="abnormal_power">Abnormal Power</option>
          <option value="rarely_used">Rarely Used</option>
          <option value="poor_power_saving">Poor Power-Saving</option>
          <option value="excessive_continuous_on">Excessive Continuous ON</option>
        </select>
      </div>

      <div className="overflow-x-auto rounded-md border border-surface-200 bg-white">
        {listQuery.loading ? (
          <div className="p-4">
            <TableSkeleton />
          </div>
        ) : !listQuery.data || listQuery.data.items.length === 0 ? (
          <EmptyState message="No anomalies detected." />
        ) : (
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead className="border-b border-surface-200 text-ink-500">
              <tr>
                <th className="px-3 py-2 font-medium">Severity</th>
                <th className="px-3 py-2 font-medium">Device</th>
                <th className="px-3 py-2 font-medium">Type</th>
                <th className="px-3 py-2 font-medium">Detected At</th>
              </tr>
            </thead>
            <tbody>
              {listQuery.data.items.map((a) => (
                <tr key={a.id} className="border-b border-surface-100 last:border-0">
                  <td className="px-3 py-2">
                    <span className={severityStyle(a.severity).textClass}>{severityStyle(a.severity).label}</span>
                  </td>
                  <td className="px-3 py-2">
                    <Link to={`/devices/${a.device_id}`} className="text-accent-700 hover:underline">
                      {a.device_id}
                    </Link>
                  </td>
                  <td className="px-3 py-2">{a.anomaly_type}</td>
                  <td className="px-3 py-2 text-ink-500">{formatUtcTimestamp(a.detected_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {listQuery.data && listQuery.data.total > pageSize && (
        <div className="flex items-center justify-between text-sm text-ink-500">
          <span>
            Page {page + 1} of {totalPages}
          </span>
          <div className="flex gap-2">
            <button
              type="button"
              disabled={page === 0}
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              className="rounded border border-surface-200 px-3 py-1 disabled:opacity-40"
            >
              Previous
            </button>
            <button
              type="button"
              disabled={page + 1 >= totalPages}
              onClick={() => setPage((p) => p + 1)}
              className="rounded border border-surface-200 px-3 py-1 disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

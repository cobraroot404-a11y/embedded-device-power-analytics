import { useState } from "react";

import { getTelemetryPage } from "../api/telemetry";
import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { TableSkeleton } from "../components/TableSkeleton";
import { useApiData } from "../hooks/useApiData";
import { formatUtcTimestamp } from "../utils/format";
import { deviceStateStyle } from "../utils/status";

export function Telemetry() {
  const [deviceId, setDeviceId] = useState("");
  const [state, setState] = useState("");
  const [page, setPage] = useState(0);
  const pageSize = 25;

  const query = useApiData(
    () =>
      getTelemetryPage({
        device_id: deviceId || undefined,
        state: state || undefined,
        limit: pageSize,
        offset: page * pageSize,
      }),
    [deviceId, state, page],
  );

  if (query.error) {
    return <ErrorState message="Unable to load telemetry." onRetry={query.refetch} />;
  }

  const totalPages = query.data ? Math.max(1, Math.ceil(query.data.total / pageSize)) : 1;

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-ink-900">Telemetry Explorer</h1>

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
          aria-label="Filter by state"
          value={state}
          onChange={(e) => {
            setState(e.target.value);
            setPage(0);
          }}
          className="rounded border border-surface-200 px-2 py-1.5 text-sm"
        >
          <option value="">All states</option>
          <option value="ON">ON</option>
          <option value="SLEEP">SLEEP</option>
          <option value="OFF">OFF</option>
        </select>
      </div>

      <div className="overflow-x-auto rounded-md border border-surface-200 bg-white">
        {query.loading ? (
          <div className="p-4">
            <TableSkeleton cols={7} />
          </div>
        ) : !query.data || query.data.items.length === 0 ? (
          <EmptyState message="No telemetry available for this reporting period." />
        ) : (
          <table className="w-full min-w-[820px] text-left text-sm">
            <thead className="border-b border-surface-200 text-ink-500">
              <tr>
                <th className="px-3 py-2 font-medium">Timestamp</th>
                <th className="px-3 py-2 font-medium">Device ID</th>
                <th className="px-3 py-2 font-medium">State</th>
                <th className="px-3 py-2 font-medium">Battery</th>
                <th className="px-3 py-2 font-medium">Power</th>
                <th className="px-3 py-2 font-medium">Boot ID</th>
              </tr>
            </thead>
            <tbody>
              {query.data.items.map((e) => (
                <tr key={e.id} className="border-b border-surface-100 last:border-0">
                  <td className="px-3 py-2 text-ink-500">{formatUtcTimestamp(e.time)}</td>
                  <td className="px-3 py-2">{e.device_id}</td>
                  <td className="px-3 py-2">
                    <span className={deviceStateStyle(e.state).textClass}>{e.state}</span>
                  </td>
                  <td className="px-3 py-2">{e.battery_percent !== null ? `${e.battery_percent}%` : "—"}</td>
                  <td className="px-3 py-2">{e.power_watts !== null ? `${e.power_watts} W` : "—"}</td>
                  <td className="px-3 py-2 text-ink-500">{e.boot_id ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {query.data && query.data.total > pageSize && (
        <div className="flex items-center justify-between text-sm text-ink-500">
          <span>
            Page {page + 1} of {totalPages} ({query.data.total} events)
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

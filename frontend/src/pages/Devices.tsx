import { useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { getDevices } from "../api/devices";
import { getFleetSummary } from "../api/analytics";
import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { TableSkeleton } from "../components/TableSkeleton";
import { useApiData } from "../hooks/useApiData";
import type { RankedDevice } from "../types";
import { formatPercent, formatRelativeTime } from "../utils/format";
import { communicationStyle, deviceStateStyle } from "../utils/status";

type SortKey = "device_id" | "usage_percent" | "last_seen";

export function Devices() {
  const [search, setSearch] = useState("");
  const [stateFilter, setStateFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("device_id");
  const [page, setPage] = useState(0);
  const pageSize = 10;

  const devicesQuery = useApiData(() => getDevices(), []);
  const summaryQuery = useApiData(() => getFleetSummary("daily"), []);

  const analyticsByDevice = useMemo(() => {
    const map = new Map<string, RankedDevice>();
    summaryQuery.data?.all_devices.forEach((d) => map.set(d.device_id, d));
    return map;
  }, [summaryQuery.data]);

  const rows = useMemo(() => {
    let list = devicesQuery.data ?? [];
    if (search) {
      list = list.filter((d) => d.device_id.toLowerCase().includes(search.toLowerCase()));
    }
    if (stateFilter) {
      list = list.filter((d) => (d.last_state ?? "UNKNOWN") === stateFilter);
    }
    if (statusFilter) {
      list = list.filter((d) => (statusFilter === "online" ? d.is_active : !d.is_active));
    }
    const sorted = [...list].sort((a, b) => {
      if (sortKey === "device_id") return a.device_id.localeCompare(b.device_id);
      if (sortKey === "last_seen") return new Date(b.last_seen).getTime() - new Date(a.last_seen).getTime();
      const av = analyticsByDevice.get(a.device_id)?.usage_percent ?? -1;
      const bv = analyticsByDevice.get(b.device_id)?.usage_percent ?? -1;
      return bv - av;
    });
    return sorted;
  }, [devicesQuery.data, search, stateFilter, statusFilter, sortKey, analyticsByDevice]);

  const pageRows = rows.slice(page * pageSize, page * pageSize + pageSize);
  const totalPages = Math.max(1, Math.ceil(rows.length / pageSize));

  if (devicesQuery.error) {
    return <ErrorState message="Unable to load devices." onRetry={devicesQuery.refetch} />;
  }

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-ink-900">Devices</h1>

      <div className="flex flex-wrap items-center gap-3">
        <input
          type="search"
          placeholder="Search device ID"
          aria-label="Search devices"
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(0);
          }}
          className="rounded border border-surface-200 px-3 py-1.5 text-sm"
        />
        <select
          aria-label="Filter by state"
          value={stateFilter}
          onChange={(e) => {
            setStateFilter(e.target.value);
            setPage(0);
          }}
          className="rounded border border-surface-200 px-2 py-1.5 text-sm"
        >
          <option value="">All states</option>
          <option value="ON">ON</option>
          <option value="SLEEP">SLEEP</option>
          <option value="OFF">OFF</option>
          <option value="UNKNOWN">UNKNOWN</option>
        </select>
        <select
          aria-label="Filter by status"
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value);
            setPage(0);
          }}
          className="rounded border border-surface-200 px-2 py-1.5 text-sm"
        >
          <option value="">All statuses</option>
          <option value="online">Online</option>
          <option value="offline">Offline</option>
        </select>
        <select
          aria-label="Sort by"
          value={sortKey}
          onChange={(e) => setSortKey(e.target.value as SortKey)}
          className="rounded border border-surface-200 px-2 py-1.5 text-sm"
        >
          <option value="device_id">Sort: Device ID</option>
          <option value="usage_percent">Sort: Usage %</option>
          <option value="last_seen">Sort: Last Seen</option>
        </select>
      </div>

      <div className="overflow-x-auto rounded-md border border-surface-200 bg-white">
        {devicesQuery.loading ? (
          <div className="p-4">
            <TableSkeleton />
          </div>
        ) : rows.length === 0 ? (
          <EmptyState message="No devices match the current filters." />
        ) : (
          <table className="w-full min-w-[720px] text-left text-sm">
            <thead className="border-b border-surface-200 text-ink-500">
              <tr>
                <th className="px-3 py-2 font-medium">Device ID</th>
                <th className="px-3 py-2 font-medium">Status</th>
                <th className="px-3 py-2 font-medium">Current State</th>
                <th className="px-3 py-2 font-medium">Last Seen</th>
                <th className="px-3 py-2 font-medium">Usage %</th>
                <th className="px-3 py-2 font-medium">Power Saving %</th>
                <th className="px-3 py-2 font-medium">Anomalies</th>
              </tr>
            </thead>
            <tbody>
              {pageRows.map((d) => {
                const analytics = analyticsByDevice.get(d.device_id);
                return (
                  <tr key={d.device_id} className="border-b border-surface-100 last:border-0 hover:bg-surface-50">
                    <td className="px-3 py-2">
                      <Link to={`/devices/${d.device_id}`} className="font-medium text-accent-700 hover:underline">
                        {d.device_id}
                      </Link>
                    </td>
                    <td className="px-3 py-2">
                      <span className={communicationStyle(d.is_active).textClass}>
                        {communicationStyle(d.is_active).label}
                      </span>
                    </td>
                    <td className="px-3 py-2">
                      <span className={deviceStateStyle(d.last_state).textClass}>
                        {deviceStateStyle(d.last_state).label}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-ink-500">{formatRelativeTime(d.last_seen)}</td>
                    <td className="px-3 py-2">{formatPercent(analytics?.usage_percent ?? null)}</td>
                    <td className="px-3 py-2">{formatPercent(analytics?.power_saving_percent ?? null)}</td>
                    <td className="px-3 py-2">{analytics?.anomaly_count ?? 0}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {rows.length > pageSize && (
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
              onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
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

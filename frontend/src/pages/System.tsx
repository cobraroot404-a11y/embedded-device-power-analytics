import { getSystemHealth } from "../api/system";
import { ErrorState } from "../components/ErrorState";
import { TableSkeleton } from "../components/TableSkeleton";
import { useApiData } from "../hooks/useApiData";
import { formatUtcTimestamp } from "../utils/format";
import { serviceStatusStyle } from "../utils/status";

const SERVICE_LABELS: Record<string, string> = {
  fastapi: "FastAPI",
  mqtt_broker: "MQTT Broker",
  telemetry_consumer: "Telemetry Consumer",
  timescaledb: "TimescaleDB",
  prometheus: "Prometheus",
  grafana: "Grafana",
  frontend: "Frontend",
};

export function System() {
  const query = useApiData(() => getSystemHealth(), [], 30_000);

  if (query.error) {
    return <ErrorState message="Unable to load system health." onRetry={query.refetch} />;
  }

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-ink-900">System Health</h1>
      {query.data && (
        <p className="text-sm text-ink-500">Checked at {formatUtcTimestamp(query.data.checked_at)}</p>
      )}

      <div className="overflow-x-auto rounded-md border border-surface-200 bg-white">
        {query.loading && !query.data ? (
          <div className="p-4">
            <TableSkeleton cols={2} />
          </div>
        ) : (
          <table className="w-full min-w-[420px] text-left text-sm">
            <thead className="border-b border-surface-200 text-ink-500">
              <tr>
                <th className="px-3 py-2 font-medium">Service</th>
                <th className="px-3 py-2 font-medium">Status</th>
                <th className="px-3 py-2 font-medium">Detail</th>
              </tr>
            </thead>
            <tbody>
              {query.data?.services.map((s) => {
                const style = serviceStatusStyle(s.status);
                return (
                  <tr key={s.name} className="border-b border-surface-100 last:border-0">
                    <td className="px-3 py-2 font-medium">{SERVICE_LABELS[s.name] ?? s.name}</td>
                    <td className="px-3 py-2">
                      <span className={style.textClass}>{style.label}</span>
                    </td>
                    <td className="px-3 py-2 text-ink-500">{s.detail ?? "—"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

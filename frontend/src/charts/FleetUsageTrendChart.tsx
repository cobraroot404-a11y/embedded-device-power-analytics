import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { FleetUsageTrend } from "../types";
import { formatUtcTimestamp } from "../utils/format";

export function FleetUsageTrendChart({ trend }: { trend: FleetUsageTrend }) {
  const data = trend.points.map((p) => ({
    time: p.bucket_start,
    label: new Date(p.bucket_start).toISOString().slice(5, 16).replace("T", " "),
    usage: p.usage_percent,
    saving: p.power_saving_percent,
    classified_seconds: p.classified_seconds,
    unknown_seconds: p.unknown_seconds,
  }));

  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="label" tick={{ fontSize: 11 }} minTickGap={24} />
        <YAxis tick={{ fontSize: 11 }} domain={[0, 100]} unit="%" />
        <Tooltip
          content={({ active, payload }) => {
            if (!active || !payload?.length) return null;
            const point = payload[0].payload as (typeof data)[number];
            return (
              <div className="rounded border border-surface-200 bg-white p-2 text-xs shadow-sm">
                <p className="font-medium">{formatUtcTimestamp(point.time)}</p>
                <p>Usage: {point.usage?.toFixed(1) ?? "—"}%</p>
                <p>Power-saving: {point.saving?.toFixed(1) ?? "—"}%</p>
                <p>Classified: {Math.round(point.classified_seconds / 60)}m</p>
                <p>Unknown: {Math.round(point.unknown_seconds / 60)}m</p>
              </div>
            );
          }}
        />
        <Line type="monotone" dataKey="usage" name="Usage %" stroke="#16a34a" dot={false} strokeWidth={2} />
        <Line
          type="monotone"
          dataKey="saving"
          name="Power-Saving %"
          stroke="#2563eb"
          dot={false}
          strokeWidth={2}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

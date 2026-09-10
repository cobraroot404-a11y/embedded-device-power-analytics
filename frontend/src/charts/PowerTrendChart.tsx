import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { PowerTrendPoint } from "../types";
import { formatUtcTimestamp } from "../utils/format";

export function PowerTrendChart({ points }: { points: PowerTrendPoint[] }) {
  const data = points.map((p) => ({
    time: p.bucket_start,
    label: new Date(p.bucket_start).toISOString().slice(5, 16).replace("T", " "),
    watts: p.avg_power_watts,
  }));

  return (
    <ResponsiveContainer width="100%" height={240}>
      <LineChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="label" tick={{ fontSize: 11 }} minTickGap={24} />
        <YAxis tick={{ fontSize: 11 }} unit="W" />
        <Tooltip
          content={({ active, payload }) => {
            if (!active || !payload?.length) return null;
            const point = payload[0].payload as (typeof data)[number];
            return (
              <div className="rounded border border-surface-200 bg-white p-2 text-xs shadow-sm">
                <p className="font-medium">{formatUtcTimestamp(point.time)}</p>
                <p>Avg power: {point.watts !== null ? `${point.watts.toFixed(2)} W` : "—"}</p>
              </div>
            );
          }}
        />
        <Line type="monotone" dataKey="watts" name="Power (W)" stroke="#d97706" dot={false} strokeWidth={2} />
      </LineChart>
    </ResponsiveContainer>
  );
}

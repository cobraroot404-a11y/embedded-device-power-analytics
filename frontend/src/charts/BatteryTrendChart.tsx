import { CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { TelemetryEvent } from "../types";

const LOW_BATTERY_THRESHOLD = 20;

export function BatteryTrendChart({ events }: { events: TelemetryEvent[] }) {
  const data = events
    .filter((e) => e.battery_percent !== null)
    .slice()
    .sort((a, b) => new Date(a.time).getTime() - new Date(b.time).getTime())
    .map((e) => ({
      label: new Date(e.time).toISOString().slice(5, 16).replace("T", " "),
      battery: e.battery_percent,
    }));

  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="label" tick={{ fontSize: 11 }} minTickGap={24} />
        <YAxis tick={{ fontSize: 11 }} domain={[0, 100]} unit="%" />
        <ReferenceLine y={LOW_BATTERY_THRESHOLD} stroke="#dc2626" strokeDasharray="4 4" label={{ value: "Low battery", fontSize: 10, fill: "#dc2626" }} />
        <Tooltip formatter={(value: number) => [`${value}%`, "Battery"]} />
        <Line type="monotone" dataKey="battery" stroke="#2563eb" dot={false} strokeWidth={2} />
      </LineChart>
    </ResponsiveContainer>
  );
}

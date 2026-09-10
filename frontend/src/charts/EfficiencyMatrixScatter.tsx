import {
  CartesianGrid,
  ReferenceLine,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ResponsiveContainer,
} from "recharts";

import type { RankedDevice } from "../types";

function quadrantColor(usage: number, saving: number): string {
  if (usage >= 50 && saving >= 50) return "#16a34a";
  if (usage >= 50 && saving < 50) return "#d97706";
  if (usage < 50 && saving >= 50) return "#2563eb";
  return "#dc2626";
}

export function EfficiencyMatrixScatter({ devices }: { devices: RankedDevice[] }) {
  const data = devices
    .filter((d) => d.usage_percent !== null && d.power_saving_percent !== null)
    .map((d) => ({
      device_id: d.device_id,
      usage: d.usage_percent as number,
      saving: d.power_saving_percent as number,
      energy: d.estimated_energy_kwh,
      anomalies: d.anomaly_count,
    }));

  return (
    <ResponsiveContainer width="100%" height={280}>
      <ScatterChart margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis
          type="number"
          dataKey="usage"
          name="Usage %"
          domain={[0, 100]}
          unit="%"
          tick={{ fontSize: 11 }}
        />
        <YAxis
          type="number"
          dataKey="saving"
          name="Power-Saving %"
          domain={[0, 100]}
          unit="%"
          tick={{ fontSize: 11 }}
        />
        <ReferenceLine x={50} stroke="#cbd5e1" />
        <ReferenceLine y={50} stroke="#cbd5e1" />
        <Tooltip
          cursor={{ strokeDasharray: "3 3" }}
          content={({ active, payload }) => {
            if (!active || !payload?.length) return null;
            const point = payload[0].payload as (typeof data)[number];
            return (
              <div className="rounded border border-surface-200 bg-white p-2 text-xs shadow-sm">
                <p className="font-medium">{point.device_id}</p>
                <p>Usage: {point.usage.toFixed(1)}%</p>
                <p>Power-saving: {point.saving.toFixed(1)}%</p>
                <p>Energy: {point.energy !== null ? `${point.energy.toFixed(2)} kWh` : "—"}</p>
                <p>Anomalies: {point.anomalies}</p>
              </div>
            );
          }}
        />
        <Scatter
          data={data}
          fill="#2563eb"
          shape={(props: { cx?: number; cy?: number; payload?: (typeof data)[number] }) => {
            const { cx, cy, payload } = props;
            if (cx === undefined || cy === undefined || !payload) return <circle />;
            return (
              <circle cx={cx} cy={cy} r={5} fill={quadrantColor(payload.usage, payload.saving)} />
            );
          }}
        />
      </ScatterChart>
    </ResponsiveContainer>
  );
}

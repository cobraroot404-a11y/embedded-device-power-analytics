import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { STATE_COLORS } from "./colors";

export interface DeviceDurationRow {
  device_id: string;
  on_seconds: number;
  sleep_seconds: number;
  off_seconds: number;
  unknown_seconds: number;
}

export function StateDurationStackedBar({ rows }: { rows: DeviceDurationRow[] }) {
  const data = rows.map((r) => ({
    device_id: r.device_id,
    ON: Math.round(r.on_seconds / 60),
    SLEEP: Math.round(r.sleep_seconds / 60),
    OFF: Math.round(r.off_seconds / 60),
    UNKNOWN: Math.round(r.unknown_seconds / 60),
  }));

  return (
    <ResponsiveContainer width="100%" height={Math.max(220, rows.length * 28)}>
      <BarChart data={data} layout="vertical" margin={{ top: 8, right: 16, bottom: 0, left: 8 }}>
        <CartesianGrid strokeDasharray="3 3" horizontal={false} />
        <XAxis type="number" tick={{ fontSize: 11 }} unit="m" />
        <YAxis type="category" dataKey="device_id" tick={{ fontSize: 11 }} width={70} />
        <Tooltip formatter={(value: number, name: string) => [`${value} min`, name]} />
        <Legend />
        <Bar dataKey="ON" stackId="s" fill={STATE_COLORS.ON} />
        <Bar dataKey="SLEEP" stackId="s" fill={STATE_COLORS.SLEEP} />
        <Bar dataKey="OFF" stackId="s" fill={STATE_COLORS.OFF} />
        <Bar dataKey="UNKNOWN" stackId="s" fill={STATE_COLORS.UNKNOWN} />
      </BarChart>
    </ResponsiveContainer>
  );
}

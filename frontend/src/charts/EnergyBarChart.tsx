import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { DevicePowerSummary } from "../types";

export function EnergyBarChart({ devices }: { devices: DevicePowerSummary[] }) {
  const data = devices
    .filter((d) => d.estimated_energy_kwh !== null)
    .map((d) => ({ device_id: d.device_id, energy: Number(d.estimated_energy_kwh?.toFixed(3)) }))
    .sort((a, b) => b.energy - a.energy);

  return (
    <ResponsiveContainer width="100%" height={Math.max(220, data.length * 26)}>
      <BarChart data={data} layout="vertical" margin={{ top: 8, right: 24, bottom: 0, left: 8 }}>
        <CartesianGrid strokeDasharray="3 3" horizontal={false} />
        <XAxis type="number" tick={{ fontSize: 11 }} unit=" kWh" />
        <YAxis type="category" dataKey="device_id" tick={{ fontSize: 11 }} width={70} />
        <Tooltip formatter={(value: number) => [`${value} kWh (estimated)`, "Energy"]} />
        <Bar dataKey="energy" fill="#2563eb" radius={[0, 3, 3, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

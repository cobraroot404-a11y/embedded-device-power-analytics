import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

import type { FleetHealthDistribution } from "../types";
import { HEALTH_COLORS } from "./colors";

export function FleetHealthDonut({ health }: { health: FleetHealthDistribution }) {
  const data = [
    { name: "Healthy", value: health.healthy },
    { name: "Warning", value: health.warning },
    { name: "Critical", value: health.critical },
    { name: "Offline", value: health.offline },
  ];

  return (
    <ResponsiveContainer width="100%" height={220}>
      <PieChart>
        <Pie data={data} dataKey="value" nameKey="name" innerRadius={55} outerRadius={85} paddingAngle={2}>
          {data.map((entry) => (
            <Cell key={entry.name} fill={HEALTH_COLORS[entry.name]} />
          ))}
        </Pie>
        <Tooltip formatter={(value: number, name: string) => [`${value} devices`, name]} />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}

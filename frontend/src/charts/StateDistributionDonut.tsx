import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

import type { FleetStates } from "../types";
import { STATE_COLORS } from "./colors";

export function StateDistributionDonut({ states }: { states: FleetStates }) {
  const data = [
    { name: "ON", value: states.on },
    { name: "SLEEP", value: states.sleep },
    { name: "OFF", value: states.off },
    { name: "UNKNOWN", value: states.unknown },
  ];

  return (
    <ResponsiveContainer width="100%" height={220}>
      <PieChart>
        <Pie
          data={data}
          dataKey="value"
          nameKey="name"
          innerRadius={55}
          outerRadius={85}
          paddingAngle={2}
        >
          {data.map((entry) => (
            <Cell key={entry.name} fill={STATE_COLORS[entry.name]} />
          ))}
        </Pie>
        <Tooltip formatter={(value: number, name: string) => [`${value} devices`, name]} />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}

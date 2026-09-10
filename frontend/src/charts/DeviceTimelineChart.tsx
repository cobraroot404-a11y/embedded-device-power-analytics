import { useState } from "react";

import type { DeviceTimeline } from "../types";
import { formatDuration } from "../utils/format";
import { STATE_COLORS } from "./colors";

interface HoverInfo {
  x: number;
  label: string;
}

function segmentColor(state: string, reason: string | null): string {
  if (reason === "gap") return "#fbbf24";
  if (reason === "reboot") return "#f97316";
  if (reason === "no_data") return "#e2e8f0";
  return STATE_COLORS[state] ?? STATE_COLORS.UNKNOWN;
}

export function DeviceTimelineChart({ timeline }: { timeline: DeviceTimeline }) {
  const [hover, setHover] = useState<HoverInfo | null>(null);
  const windowStart = new Date(timeline.window_start).getTime();
  const windowEnd = new Date(timeline.window_end).getTime();
  const totalMs = Math.max(1, windowEnd - windowStart);

  if (timeline.segments.length === 0) {
    return <p className="text-sm text-ink-500">No telemetry available for this reporting period.</p>;
  }

  return (
    <div>
      <div className="relative h-10 w-full overflow-hidden rounded border border-surface-200">
        {timeline.segments.map((seg, i) => {
          const start = new Date(seg.start).getTime();
          const end = new Date(seg.end).getTime();
          const widthPct = (Math.max(0, end - start) / totalMs) * 100;
          const durationLabel = formatDuration((end - start) / 1000);
          const label = `${seg.reason === "gap" ? "Communication gap" : seg.reason === "reboot" ? "Reboot boundary" : seg.reason === "no_data" ? "No telemetry" : seg.state} — ${durationLabel}`;
          return (
            <div
              key={i}
              style={{ width: `${widthPct}%`, backgroundColor: segmentColor(seg.state, seg.reason) }}
              className="inline-block h-full align-top"
              title={label}
              onMouseEnter={(e) => setHover({ x: e.clientX, label })}
              onMouseLeave={() => setHover(null)}
            />
          );
        })}
        {timeline.reboots.map((r, i) => {
          const offsetPct = ((new Date(r).getTime() - windowStart) / totalMs) * 100;
          return (
            <div
              key={i}
              className="absolute top-0 h-full w-0.5 bg-ink-900"
              style={{ left: `${offsetPct}%` }}
              title={`Reboot at ${r}`}
            />
          );
        })}
      </div>
      {hover && <p className="mt-1 text-xs text-ink-700">{hover.label}</p>}
      <div className="mt-2 flex flex-wrap gap-3 text-xs text-ink-500">
        <LegendDot color={STATE_COLORS.ON} label="ON" />
        <LegendDot color={STATE_COLORS.SLEEP} label="SLEEP" />
        <LegendDot color={STATE_COLORS.OFF} label="OFF" />
        <LegendDot color="#fbbf24" label="Communication gap" />
        <LegendDot color="#f97316" label="Reboot" />
        <LegendDot color="#e2e8f0" label="No telemetry" />
      </div>
    </div>
  );
}

function LegendDot({ color, label }: { color: string; label: string }) {
  return (
    <span className="flex items-center gap-1">
      <span className="h-2 w-2 rounded-full" style={{ backgroundColor: color }} />
      {label}
    </span>
  );
}

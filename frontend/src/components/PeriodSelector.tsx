import type { Period } from "../types";

const OPTIONS: { value: Period; label: string }[] = [
  { value: "hourly", label: "Last Hour" },
  { value: "daily", label: "24H" },
  { value: "weekly", label: "7D" },
  { value: "monthly", label: "30D" },
];

interface PeriodSelectorProps {
  value: Period;
  onChange: (period: Period) => void;
}

export function PeriodSelector({ value, onChange }: PeriodSelectorProps) {
  return (
    <div className="inline-flex rounded-md border border-surface-200 bg-white p-0.5" role="group" aria-label="Time period">
      {OPTIONS.map((opt) => (
        <button
          key={opt.value}
          type="button"
          onClick={() => onChange(opt.value)}
          aria-pressed={value === opt.value}
          className={`rounded px-3 py-1 text-sm font-medium ${
            value === opt.value ? "bg-ink-900 text-white" : "text-ink-700 hover:bg-surface-100"
          }`}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}

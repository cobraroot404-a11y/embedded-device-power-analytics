const OPTIONS: { value: number; label: string }[] = [
  { value: 0, label: "Off" },
  { value: 10_000, label: "10 sec" },
  { value: 30_000, label: "30 sec" },
  { value: 60_000, label: "60 sec" },
];

interface AutoRefreshSelectorProps {
  value: number;
  onChange: (ms: number) => void;
}

export function AutoRefreshSelector({ value, onChange }: AutoRefreshSelectorProps) {
  return (
    <label className="flex items-center gap-2 text-sm text-ink-700">
      Auto-refresh
      <select
        className="rounded border border-surface-200 bg-white px-2 py-1 text-sm"
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
      >
        {OPTIONS.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </label>
  );
}

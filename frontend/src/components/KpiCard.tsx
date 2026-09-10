interface KpiCardProps {
  label: string;
  value: string;
  hint?: string;
}

export function KpiCard({ label, value, hint }: KpiCardProps) {
  return (
    <div className="rounded-md border border-surface-200 bg-white p-4">
      <p className="text-2xl font-semibold text-ink-900">{value}</p>
      <p className="mt-1 text-sm text-ink-500">{label}</p>
      {hint && <p className="mt-1 text-xs text-ink-500">{hint}</p>}
    </div>
  );
}

export function KpiCardSkeleton() {
  return (
    <div className="rounded-md border border-surface-200 bg-white p-4">
      <div className="h-7 w-16 animate-pulse rounded bg-surface-200" />
      <div className="mt-2 h-4 w-24 animate-pulse rounded bg-surface-200" />
    </div>
  );
}

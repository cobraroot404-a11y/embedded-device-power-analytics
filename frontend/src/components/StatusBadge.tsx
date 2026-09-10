import type { StatusStyle } from "../utils/status";

export function StatusBadge({ style }: { style: StatusStyle }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-sm">
      <span aria-hidden="true" className={`h-2 w-2 rounded-full ${style.dotClass}`} />
      <span className={style.textClass}>{style.label}</span>
    </span>
  );
}

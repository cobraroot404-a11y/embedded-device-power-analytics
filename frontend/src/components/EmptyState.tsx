export function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex h-40 items-center justify-center rounded-md border border-dashed border-surface-200 text-sm text-ink-500">
      {message}
    </div>
  );
}

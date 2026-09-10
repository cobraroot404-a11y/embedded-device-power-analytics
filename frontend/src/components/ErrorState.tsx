interface ErrorStateProps {
  message: string;
  onRetry?: () => void;
}

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div
      role="alert"
      className="flex h-40 flex-col items-center justify-center gap-2 rounded-md border border-status-critical/30 bg-status-critical/5 text-sm text-status-critical"
    >
      <p>{message}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="rounded border border-status-critical/40 px-3 py-1 text-xs font-medium hover:bg-status-critical/10"
        >
          Retry
        </button>
      )}
    </div>
  );
}

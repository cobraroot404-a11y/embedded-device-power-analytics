import { useCallback, useEffect, useRef, useState } from "react";

interface UseApiDataResult<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  lastUpdated: Date | null;
  refetch: () => void;
}

/** Fetches data on mount and whenever `deps` change, with optional
 * auto-refresh that pauses while the browser tab is hidden so the API isn't
 * hammered by inactive tabs. */
export function useApiData<T>(
  fetcher: () => Promise<T>,
  deps: unknown[],
  refreshMs: number | null = null,
): UseApiDataResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  const load = useCallback(() => {
    let cancelled = false;
    setLoading(true);
    fetcherRef
      .current()
      .then((result) => {
        if (cancelled) return;
        setData(result);
        setError(null);
        setLastUpdated(new Date());
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Unable to load data.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => load(), [load]);

  useEffect(() => {
    if (!refreshMs) return;
    const interval = setInterval(() => {
      if (document.hidden) return;
      load();
    }, refreshMs);
    return () => clearInterval(interval);
  }, [refreshMs, load]);

  return { data, loading, error, lastUpdated, refetch: load };
}

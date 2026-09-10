// Defaults to a same-origin "/api" path, proxied to the backend by nginx in
// production (see frontend/nginx.conf) — no CORS needed. Override with
// VITE_API_BASE_URL for `npm run dev` against a bare API (e.g. http://localhost:8000).
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";

export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function buildQuery(params?: Record<string, string | number | undefined>): string {
  if (!params) return "";
  const entries = Object.entries(params).filter(([, v]) => v !== undefined && v !== "");
  if (entries.length === 0) return "";
  const search = new URLSearchParams(entries.map(([k, v]) => [k, String(v)]));
  return `?${search.toString()}`;
}

export async function apiGet<T>(
  path: string,
  params?: Record<string, string | number | undefined>,
): Promise<T> {
  const url = `${BASE_URL}${path}${buildQuery(params)}`;
  let response: Response;
  try {
    response = await fetch(url);
  } catch {
    throw new ApiError("Unable to reach the API. Check that the backend is running.");
  }
  if (!response.ok) {
    throw new ApiError(`Request to ${path} failed`, response.status);
  }
  return (await response.json()) as T;
}

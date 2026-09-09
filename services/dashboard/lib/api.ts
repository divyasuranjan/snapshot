import type {
  DevicesResponse,
  GeoResponse,
  ReferrersResponse,
  TimeRange,
  TimeseriesResponse,
} from "./types";

export type Result<T> = { ok: true; data: T } | { ok: false; error: string };

// Server-only: the dashboard's backend talks to analytics-worker directly.
// The browser never sees this URL or calls the service itself.
const ANALYTICS_WORKER_URL = process.env.ANALYTICS_WORKER_URL ?? "http://localhost:8098";

async function getJSON<T>(path: string): Promise<Result<T>> {
  try {
    const res = await fetch(`${ANALYTICS_WORKER_URL}${path}`, { cache: "no-store" });
    if (!res.ok) {
      return { ok: false, error: `analytics-worker responded with ${res.status}` };
    }
    return { ok: true, data: (await res.json()) as T };
  } catch {
    return { ok: false, error: "Could not reach analytics-worker" };
  }
}

export function rangeToParams(range: TimeRange): { interval: "hour" | "day"; hours: number } {
  switch (range) {
    case "24h":
      return { interval: "hour", hours: 24 };
    case "7d":
      return { interval: "day", hours: 24 * 7 };
    case "30d":
      return { interval: "day", hours: 24 * 30 };
  }
}

export function getTimeseries(range: TimeRange): Promise<Result<TimeseriesResponse>> {
  const { interval, hours } = rangeToParams(range);
  return getJSON<TimeseriesResponse>(`/api/stats/timeseries?interval=${interval}&hours=${hours}`);
}

export function getReferrers(range: TimeRange, limit = 8): Promise<Result<ReferrersResponse>> {
  const { hours } = rangeToParams(range);
  return getJSON<ReferrersResponse>(`/api/stats/referrers?hours=${hours}&limit=${limit}`);
}

export function getDevices(range: TimeRange): Promise<Result<DevicesResponse>> {
  const { hours } = rangeToParams(range);
  return getJSON<DevicesResponse>(`/api/stats/devices?hours=${hours}`);
}

export function getGeo(range: TimeRange, cityLimit = 8): Promise<Result<GeoResponse>> {
  const { hours } = rangeToParams(range);
  return getJSON<GeoResponse>(`/api/stats/geo?hours=${hours}&city_limit=${cityLimit}`);
}

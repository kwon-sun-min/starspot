// 얇은 fetch 래퍼. 프론트는 외부 API 를 직접 호출하지 않고 항상 /api 를 경유한다.

const BASE = "/api/v1";

async function get<T>(path: string, params?: Record<string, string | number>): Promise<T> {
  const url = new URL(BASE + path, window.location.origin);
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      url.searchParams.set(k, String(v));
    }
  }
  const res = await fetch(url.toString(), { headers: { Accept: "application/json" } });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${body || res.statusText}`);
  }
  return (await res.json()) as T;
}

import type {
  AstroResponse,
  ForecastResponse,
  SkyViewResponse,
  SpotDetail,
  SpotSummary,
} from "./types";

export const api = {
  listSpots: (
    lat: number,
    lon: number,
    radiusKm: number,
    opts: { limit?: number; category?: string; mode?: string } = {},
  ) => {
    const params: Record<string, string | number> = {
      lat,
      lon,
      radius_km: radiusKm,
      limit: opts.limit ?? 50,
      mode: opts.mode ?? "darkness",
    };
    if (opts.category) params.category = opts.category;
    return get<SpotSummary[]>("/spots", params);
  },

  getSpot: (id: number) => get<SpotDetail>(`/spots/${id}`),

  getForecast: (id: number, date?: string) =>
    get<ForecastResponse>(`/spots/${id}/forecast`, date ? { date } : undefined),

  getAstro: (lat: number, lon: number, date?: string) =>
    get<AstroResponse>("/astro", date ? { lat, lon, date } : { lat, lon }),

  getSkyView: (id: number, at?: string) =>
    get<SkyViewResponse>(`/spots/${id}/skyview`, at ? { at } : undefined),
};

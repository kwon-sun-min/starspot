// 얇은 fetch 래퍼.
// API base 결정 순서:
//   1) 런타임 주입값 window.__ENV__.API_BASE (컨테이너 배포)
//   2) 빌드 환경변수 VITE_API_BASE (Vercel 등, 백엔드 절대 URL)
//   3) 기본값 "/api/v1" (로컬 compose: nginx 가 /api 를 백엔드로 프록시)
// 절대 URL(예: https://api.example.com)이면 뒤에 /api/v1 을 붙인다.
function resolveBase(): string {
  const runtime =
    typeof window !== "undefined" ? window.__ENV__?.API_BASE : undefined;
  const buildTime = import.meta.env.VITE_API_BASE as string | undefined;
  const raw = (runtime || buildTime || "").trim();
  if (!raw) return "/api/v1";
  const trimmed = raw.replace(/\/+$/, "");
  return trimmed.endsWith("/api/v1") ? trimmed : `${trimmed}/api/v1`;
}

const BASE = resolveBase();

async function get<T>(path: string, params?: Record<string, string | number>): Promise<T> {
  // BASE 가 절대 URL 이면 그대로, 상대경로면 현재 origin 기준.
  const isAbsolute = /^https?:\/\//i.test(BASE);
  const url = new URL(BASE + path, isAbsolute ? undefined : window.location.origin);
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

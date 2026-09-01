// 백엔드 스키마(app/schemas/spot.py)와 대응하는 타입.

export interface Breakdown {
  darkness: number;
  cloud: number;
  moon: number;
  access: number;
}

export interface SpotSummary {
  id: number;
  name: string;
  category: SpotCategory;
  lat: number;
  lon: number;
  distance_km: number;
  score: number;
  breakdown: Breakdown;
  bortle: number | null;
  best_hour: string | null;
}

export interface SpotDetail {
  id: number;
  name: string;
  category: SpotCategory;
  address: string | null;
  lat: number;
  lon: number;
  elevation_m: number | null;
  radiance: number | null;
  darkness_score: number | null;
  bortle: number | null;
}

export interface HourlyScore {
  hour: string;
  score: number;
  cloud: number;
  moon: number;
}

export interface ForecastResponse {
  spot_id: number;
  date: string;
  hourly: HourlyScore[];
  best_hour: string | null;
  best_score: number;
  stale: boolean;
}

export interface AstroResponse {
  sunset: string | null;
  sunrise: string | null;
  moonrise: string | null;
  moonset: string | null;
  moon_phase_deg: number;
  moon_illumination: number;
}

export type SpotCategory = "observatory" | "campsite" | "viewpoint" | "park";

export interface SkyStar {
  name: string;
  alt: number;
  az: number;
  mag: number;
}

export interface SkyPoint {
  alt: number;
  az: number;
}

export interface SkyConstellation {
  name: string;
  name_ko: string;
  points: SkyPoint[];
  lines: [number, number][];
}

export interface SkyViewResponse {
  spot_id: number;
  at: string;
  stars: SkyStar[];
  constellations: SkyConstellation[];
}

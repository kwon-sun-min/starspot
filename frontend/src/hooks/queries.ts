import { useQuery } from "@tanstack/react-query";

import { api } from "../api/client";

export function useSpots(
  lat: number,
  lon: number,
  radiusKm: number,
  opts: { category?: string; mode?: string; enabled?: boolean } = {},
) {
  const { category, mode = "darkness", enabled = true } = opts;
  return useQuery({
    queryKey: ["spots", lat, lon, radiusKm, category ?? "all", mode],
    queryFn: () => api.listSpots(lat, lon, radiusKm, { category, mode }),
    enabled,
    staleTime: 5 * 60 * 1000,
  });
}

export function useSpot(id: number | null) {
  return useQuery({
    queryKey: ["spot", id],
    queryFn: () => api.getSpot(id as number),
    enabled: id != null,
  });
}

export function useForecast(id: number | null, date?: string) {
  return useQuery({
    queryKey: ["forecast", id, date ?? "today"],
    queryFn: () => api.getForecast(id as number, date),
    enabled: id != null,
    staleTime: 30 * 60 * 1000,
  });
}

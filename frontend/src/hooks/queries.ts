import { useQuery } from "@tanstack/react-query";

import { api } from "../api/client";

export function useSpots(lat: number, lon: number, radiusKm: number, enabled = true) {
  return useQuery({
    queryKey: ["spots", lat, lon, radiusKm],
    queryFn: () => api.listSpots(lat, lon, radiusKm),
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

export function useForecast(id: number | null) {
  return useQuery({
    queryKey: ["forecast", id],
    queryFn: () => api.getForecast(id as number),
    enabled: id != null,
    staleTime: 30 * 60 * 1000,
  });
}

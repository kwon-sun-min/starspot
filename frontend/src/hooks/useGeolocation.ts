import { useEffect, useState } from "react";

// 위치 권한 거부 시 서울시청 기본값.
export const SEOUL_CITY_HALL = { lat: 37.5665, lon: 126.978 };

export interface GeoState {
  lat: number;
  lon: number;
  denied: boolean;
  loading: boolean;
}

export function useGeolocation(): GeoState {
  const [state, setState] = useState<GeoState>({
    ...SEOUL_CITY_HALL,
    denied: false,
    loading: true,
  });

  useEffect(() => {
    if (!("geolocation" in navigator)) {
      setState((s) => ({ ...s, denied: true, loading: false }));
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setState({
          lat: Number(pos.coords.latitude.toFixed(6)),
          lon: Number(pos.coords.longitude.toFixed(6)),
          denied: false,
          loading: false,
        });
      },
      () => {
        // 거부 또는 실패 -> 서울시청 기본값
        setState({ ...SEOUL_CITY_HALL, denied: true, loading: false });
      },
      { timeout: 8000, maximumAge: 300000 },
    );
  }, []);

  return state;
}

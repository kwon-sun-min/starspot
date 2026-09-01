import { useEffect, useRef } from "react";

import type { SpotSummary } from "../api/types";
import { useKakaoLoader } from "../hooks/useKakaoLoader";
import { scoreColor } from "../lib/score";

interface Props {
  center: { lat: number; lon: number };
  spots: SpotSummary[];
  selectedId: number | null;
  onSelect: (id: number) => void;
}

// 점수 색상으로 채운 원형 마커를 SVG data-URI 로 생성.
function markerImageSrc(score: number): string {
  const color = scoreColor(score);
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="34" height="42" viewBox="0 0 34 42">
      <path d="M17 41C17 41 32 25 32 15A15 15 0 1 0 2 15C2 25 17 41 17 41Z"
            fill="${color}" stroke="white" stroke-width="2"/>
      <text x="17" y="20" text-anchor="middle" font-size="12" font-weight="700"
            fill="#0b1020" font-family="sans-serif">${score}</text>
    </svg>`;
  return "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg);
}

export function KakaoMap({ center, spots, selectedId, onSelect }: Props) {
  const { ready, error } = useKakaoLoader();
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<any>(null);
  const markersRef = useRef<any[]>([]);
  const meMarkerRef = useRef<any>(null);

  // 지도 초기화
  useEffect(() => {
    if (!ready || !containerRef.current || mapRef.current) return;
    const kakao = window.kakao;
    mapRef.current = new kakao.maps.Map(containerRef.current, {
      center: new kakao.maps.LatLng(center.lat, center.lon),
      level: 9,
    });
  }, [ready, center.lat, center.lon]);

  // 내 위치 마커 + 중심 이동
  useEffect(() => {
    if (!ready || !mapRef.current) return;
    const kakao = window.kakao;
    const pos = new kakao.maps.LatLng(center.lat, center.lon);
    mapRef.current.setCenter(pos);
    if (meMarkerRef.current) meMarkerRef.current.setMap(null);
    meMarkerRef.current = new kakao.maps.Marker({
      position: pos,
      map: mapRef.current,
      title: "내 위치",
      zIndex: 100,
    });
  }, [ready, center.lat, center.lon]);

  // 후보지 마커 갱신
  useEffect(() => {
    if (!ready || !mapRef.current) return;
    const kakao = window.kakao;
    markersRef.current.forEach((m) => m.setMap(null));
    markersRef.current = spots.map((s) => {
      const size = s.id === selectedId ? 44 : 34;
      const image = new kakao.maps.MarkerImage(
        markerImageSrc(s.score),
        new kakao.maps.Size(size, size * 1.24),
      );
      const marker = new kakao.maps.Marker({
        position: new kakao.maps.LatLng(s.lat, s.lon),
        map: mapRef.current,
        image,
        title: `${s.name} (${s.score})`,
        zIndex: s.id === selectedId ? 50 : 10,
      });
      kakao.maps.event.addListener(marker, "click", () => onSelect(s.id));
      return marker;
    });
  }, [ready, spots, selectedId, onSelect]);

  if (error) {
    return (
      <div className="map-fallback" role="alert">
        지도를 불러오지 못했어요.<br />
        <small>{error}</small>
      </div>
    );
  }

  return <div ref={containerRef} className="map-container" aria-label="후보지 지도" />;
}

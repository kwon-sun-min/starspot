import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { KakaoMap } from "../components/KakaoMap";
import { RadiusSlider } from "../components/RadiusSlider";
import { RankingList } from "../components/RankingList";
import { RankingSkeleton } from "../components/Skeleton";
import { useSpots } from "../hooks/queries";
import { useGeolocation } from "../hooks/useGeolocation";

export function MainPage() {
  const geo = useGeolocation();
  const navigate = useNavigate();
  const [radius, setRadius] = useState(100);
  const [selectedId, setSelectedId] = useState<number | null>(null);

  const { data: spots, isLoading, isError, error } = useSpots(
    geo.lat,
    geo.lon,
    radius,
    !geo.loading,
  );

  const openDetail = (id: number) => navigate(`/spot/${id}`);

  return (
    <div className="main-layout">
      <section className="map-pane">
        <KakaoMap
          center={{ lat: geo.lat, lon: geo.lon }}
          spots={spots ?? []}
          selectedId={selectedId}
          onSelect={setSelectedId}
        />
        <div className="map-overlay">
          <RadiusSlider value={radius} onChange={setRadius} />
          {geo.denied && (
            <p className="notice">위치 권한이 없어 서울시청 기준으로 표시 중이에요.</p>
          )}
        </div>
      </section>

      <aside className="ranking-pane">
        <header className="ranking-header">
          <h1>오늘 밤 별 보기 좋은 곳</h1>
          <p className="sub">반경 {radius}km · 점수 높은 순</p>
        </header>

        {isLoading || geo.loading ? (
          <RankingSkeleton />
        ) : isError ? (
          <p className="error" role="alert">
            불러오기 실패: {(error as Error)?.message}
          </p>
        ) : (
          <RankingList
            spots={spots ?? []}
            selectedId={selectedId}
            onSelect={setSelectedId}
            onOpenDetail={openDetail}
          />
        )}
      </aside>
    </div>
  );
}

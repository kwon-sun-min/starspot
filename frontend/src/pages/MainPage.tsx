import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { KakaoMap } from "../components/KakaoMap";
import { RadiusSlider } from "../components/RadiusSlider";
import { RankingList } from "../components/RankingList";
import { RankingSkeleton } from "../components/Skeleton";
import { useSpots } from "../hooks/queries";
import { useGeolocation } from "../hooks/useGeolocation";

const CATEGORIES: { key: string; label: string }[] = [
  { key: "observatory", label: "천문대" },
  { key: "park", label: "공원" },
  { key: "viewpoint", label: "전망대" },
  { key: "campsite", label: "야영장" },
];

export function MainPage() {
  const geo = useGeolocation();
  const navigate = useNavigate();
  const [radius, setRadius] = useState(100);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [selectedCats, setSelectedCats] = useState<string[]>([]);
  const [nearby, setNearby] = useState(false);

  const { data: spots, isLoading, isError, error } = useSpots(geo.lat, geo.lon, radius, {
    category: selectedCats.length ? selectedCats.join(",") : undefined,
    mode: nearby ? "nearby" : "darkness",
    enabled: !geo.loading,
  });

  const toggleCat = (key: string) =>
    setSelectedCats((prev) =>
      prev.includes(key) ? prev.filter((c) => c !== key) : [...prev, key],
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
          <p className="sub">
            반경 {radius}km · {nearby ? "가까운 순 우대" : "점수 높은 순"}
          </p>

          <div className="mode-toggle">
            <button
              className={!nearby ? "active" : ""}
              onClick={() => setNearby(false)}
            >
              관측 품질
            </button>
            <button
              className={nearby ? "active" : ""}
              onClick={() => setNearby(true)}
            >
              가까운 곳 우선
            </button>
          </div>

          <div className="cat-filter">
            {CATEGORIES.map((c) => (
              <button
                key={c.key}
                className={`cat-chip${selectedCats.includes(c.key) ? " on" : ""}`}
                onClick={() => toggleCat(c.key)}
              >
                {c.label}
              </button>
            ))}
          </div>
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

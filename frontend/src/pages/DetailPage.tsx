import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { SkeletonLine } from "../components/Skeleton";
import { SkyView } from "../components/SkyView";
import { useForecast, useSkyView, useSpot } from "../hooks/queries";
import { bortleGuide, CATEGORY_LABEL, scoreAdvice, scoreColor } from "../lib/score";

function hourLabel(iso: string): string {
  const d = new Date(iso);
  return `${String(d.getHours()).padStart(2, "0")}시`;
}

// KST 기준 오늘/내일/모레 날짜(YYYY-MM-DD) 옵션 생성.
function dateOptions(): { key: string; label: string; value: string }[] {
  const fmt = (offset: number) => {
    const d = new Date();
    d.setDate(d.getDate() + offset);
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return `${y}-${m}-${day}`;
  };
  return [
    { key: "today", label: "오늘 밤", value: fmt(0) },
    { key: "tomorrow", label: "내일 밤", value: fmt(1) },
    { key: "day2", label: "모레 밤", value: fmt(2) },
  ];
}

export function DetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const spotId = id ? Number(id) : null;
  const spot = useSpot(spotId);

  // ESC 로 목록으로 복귀
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") navigate("/");
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [navigate]);

  const dates = dateOptions();
  const [dateKey, setDateKey] = useState("today");
  const [showConstellations, setShowConstellations] = useState(true);
  const selectedDate = dates.find((d) => d.key === dateKey)!;
  // "오늘"은 date 미지정(백엔드 기본값), 그 외는 명시적으로 전달
  const forecast = useForecast(spotId, dateKey === "today" ? undefined : selectedDate.value);

  const chartData =
    forecast.data?.hourly.map((h) => ({
      time: hourLabel(h.hour),
      score: h.score,
      cloud: h.cloud,
    })) ?? [];

  // 밤하늘: 최적 시각(없으면 선택 날짜 22시) 기준
  const skyAt =
    forecast.data?.best_hour ??
    (dateKey === "today" ? undefined : `${selectedDate.value}T22:00:00+09:00`);
  const skyview = useSkyView(spotId, skyAt ?? undefined);

  const guide = bortleGuide(spot.data?.bortle ?? null);
  const bestScore = forecast.data?.best_score ?? 0;

  const directionsUrl =
    spot.data &&
    `https://map.kakao.com/link/to/${encodeURIComponent(spot.data.name)},${spot.data.lat},${spot.data.lon}`;

  return (
    <div className="detail-page">
      <Link to="/" className="back-link">
        ← 목록으로
      </Link>

      {spot.isLoading ? (
        <div className="detail-head">
          <SkeletonLine width="50%" />
          <SkeletonLine width="30%" />
        </div>
      ) : spot.isError ? (
        <p className="error" role="alert">
          후보지를 불러오지 못했어요.
        </p>
      ) : spot.data ? (
        <>
          <header className="detail-head">
            <h1>{spot.data.name}</h1>
            <p className="sub">
              {CATEGORY_LABEL[spot.data.category] ?? spot.data.category}
              {spot.data.address ? ` · ${spot.data.address}` : ""}
            </p>
            <div className="detail-tags">
              {spot.data.bortle != null && <span className="tag">Bortle {spot.data.bortle}</span>}
              {spot.data.elevation_m != null && (
                <span className="tag">고도 {spot.data.elevation_m}m</span>
              )}
              {spot.data.darkness_score != null && (
                <span className="tag">암흑도 {spot.data.darkness_score}</span>
              )}
            </div>
            {directionsUrl && (
              <a className="directions" href={directionsUrl} target="_blank" rel="noreferrer">
                카카오맵 길찾기
              </a>
            )}
          </header>

          {/* 관측 맥락 가이드 */}
          <section className="guide-card">
            <div className="guide-badge" style={{ borderColor: scoreColor(bestScore) }}>
              <span className="guide-score" style={{ color: scoreColor(bestScore) }}>
                {bestScore}
              </span>
              <span className="guide-score-label">오늘 밤 점수</span>
            </div>
            <div className="guide-body">
              <div className="guide-title">{guide.title}</div>
              <p className="guide-desc">{guide.desc}</p>
              {forecast.data && <p className="guide-advice">{scoreAdvice(bestScore)}</p>}
            </div>
          </section>

          <section className="chart-section">
            <div className="chart-header">
              <h2>시간대별 관측 점수 (일몰~일출)</h2>
              <div className="date-picker">
                {dates.map((d) => (
                  <button
                    key={d.key}
                    className={`date-chip${d.key === dateKey ? " on" : ""}`}
                    onClick={() => setDateKey(d.key)}
                  >
                    {d.label}
                  </button>
                ))}
              </div>
            </div>

            {forecast.isLoading ? (
              <SkeletonLine width="100%" />
            ) : chartData.length === 0 ? (
              <p className="empty">이 밤에는 표시할 관측 구간이 없어요.</p>
            ) : (
              <>
                {forecast.data?.stale && (
                  <p className="notice">
                    기상청 최신 예보를 받지 못해 직전 캐시로 표시 중이에요.
                  </p>
                )}
                <ResponsiveContainer width="100%" height={260}>
                  <LineChart data={chartData} margin={{ top: 8, right: 16, left: -16, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#26304a" />
                    <XAxis dataKey="time" stroke="#8aa0c6" fontSize={12} />
                    <YAxis domain={[0, 100]} stroke="#8aa0c6" fontSize={12} />
                    <Tooltip
                      contentStyle={{ background: "#131a2e", border: "1px solid #26304a" }}
                    />
                    <Line
                      type="monotone"
                      dataKey="score"
                      stroke="#22d3ee"
                      strokeWidth={2}
                      dot={{ r: 3 }}
                      name="점수"
                    />
                  </LineChart>
                </ResponsiveContainer>
                <p className="best-hour">
                  최적 시각:{" "}
                  <strong style={{ color: scoreColor(bestScore) }}>
                    {forecast.data?.best_hour ? hourLabel(forecast.data.best_hour) : "-"} (
                    {bestScore})
                  </strong>
                </p>
              </>
            )}
          </section>

          <section className="sky-section">
            <div className="chart-header">
              <h2>
                이 시각 밤하늘
                {skyAt && <span className="sky-time"> · {hourLabel(skyAt)} 기준</span>}
              </h2>
              <button
                className={`cat-chip${showConstellations ? " on" : ""}`}
                onClick={() => setShowConstellations((v) => !v)}
              >
                별자리 {showConstellations ? "켜짐" : "꺼짐"}
              </button>
            </div>
            {skyview.isLoading ? (
              <SkeletonLine width="100%" />
            ) : (skyview.data?.stars.length ?? 0) === 0 ? (
              <p className="empty">이 시각에는 지평선 위 밝은 별이 없어요.</p>
            ) : (
              <div className="sky-wrap">
                <SkyView
                  stars={skyview.data!.stars}
                  constellations={skyview.data!.constellations}
                  showConstellations={showConstellations}
                />
                <p className="sky-caption">
                  천정이 가운데, 지평선이 바깥 원이에요. 밝은 별일수록 크게 표시됩니다.
                  {showConstellations && skyview.data!.constellations.length > 0 && (
                    <> 오늘 밤 별자리 {skyview.data!.constellations.length}개가 보여요.</>
                  )}
                </p>
              </div>
            )}
          </section>
        </>
      ) : null}
    </div>
  );
}

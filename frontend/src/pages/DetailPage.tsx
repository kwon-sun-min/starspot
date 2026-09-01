import { Link, useParams } from "react-router-dom";
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
import { useForecast, useSpot } from "../hooks/queries";
import { CATEGORY_LABEL, scoreColor } from "../lib/score";

function hourLabel(iso: string): string {
  const d = new Date(iso);
  return `${String(d.getHours()).padStart(2, "0")}시`;
}

export function DetailPage() {
  const { id } = useParams();
  const spotId = id ? Number(id) : null;
  const spot = useSpot(spotId);
  const forecast = useForecast(spotId);

  const chartData =
    forecast.data?.hourly.map((h) => ({
      time: hourLabel(h.hour),
      score: h.score,
      cloud: h.cloud,
    })) ?? [];

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

          <section className="chart-section">
            <h2>시간대별 관측 점수 (일몰~일출)</h2>
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
                  <strong style={{ color: scoreColor(forecast.data?.best_score ?? 0) }}>
                    {forecast.data?.best_hour ? hourLabel(forecast.data.best_hour) : "-"} (
                    {forecast.data?.best_score})
                  </strong>
                </p>
              </>
            )}
          </section>
        </>
      ) : null}
    </div>
  );
}

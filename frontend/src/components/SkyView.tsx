import { useEffect, useRef } from "react";

import type { SkyConstellation, SkyStar } from "../api/types";

interface Props {
  stars: SkyStar[];
  constellations?: SkyConstellation[];
  showConstellations?: boolean;
  size?: number;
}

// 지평좌표(alt, az)를 원형 스카이돔에 투영한다.
// 천정(alt=90)이 중심, 지평선(alt=0)이 원 가장자리. 방위는 북=위, 동=오른쪽.
function project(alt: number, az: number, radius: number): { x: number; y: number } {
  const r = ((90 - alt) / 90) * radius; // 천정에서의 거리
  const theta = (az * Math.PI) / 180; // 북 기준 시계방향
  // 북을 위(-y), 동을 오른쪽(+x)로
  const x = r * Math.sin(theta);
  const y = -r * Math.cos(theta);
  return { x, y };
}

// 등급 -> 점 반지름 (밝을수록 큼)
function starRadius(mag: number): number {
  return Math.max(0.8, 3.2 - mag * 0.7);
}

export function SkyView({
  stars,
  constellations = [],
  showConstellations = true,
  size = 320,
}: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const dpr = window.devicePixelRatio || 1;
    canvas.width = size * dpr;
    canvas.height = size * dpr;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.scale(dpr, dpr);

    const cx = size / 2;
    const cy = size / 2;
    const radius = size / 2 - 10;

    // 배경 (밤하늘 원)
    ctx.clearRect(0, 0, size, size);
    const grad = ctx.createRadialGradient(cx, cy, radius * 0.1, cx, cy, radius);
    grad.addColorStop(0, "#0d1530");
    grad.addColorStop(1, "#05070f");
    ctx.beginPath();
    ctx.arc(cx, cy, radius, 0, Math.PI * 2);
    ctx.fillStyle = grad;
    ctx.fill();

    // 지평선 원 테두리
    ctx.strokeStyle = "#26304a";
    ctx.lineWidth = 1;
    ctx.stroke();

    // 고도 30/60도 보조원
    ctx.strokeStyle = "rgba(38,48,74,0.6)";
    for (const alt of [30, 60]) {
      const rr = ((90 - alt) / 90) * radius;
      ctx.beginPath();
      ctx.arc(cx, cy, rr, 0, Math.PI * 2);
      ctx.stroke();
    }

    // 방위 라벨 (N/E/S/W)
    ctx.fillStyle = "#8aa0c6";
    ctx.font = "11px sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText("N", cx, cy - radius + 8);
    ctx.fillText("S", cx, cy + radius - 8);
    ctx.fillText("E", cx + radius - 8, cy);
    ctx.fillText("W", cx - radius + 8, cy);

    // 별자리 선/이름 (별보다 먼저 그려 별이 위에 오게)
    if (showConstellations) {
      ctx.strokeStyle = "rgba(120,160,230,0.45)";
      ctx.lineWidth = 1;
      ctx.font = "10px sans-serif";
      ctx.textAlign = "center";
      for (const con of constellations) {
        // 선: 양 끝 별이 모두 지평선 위(alt>0)일 때만 연결
        for (const [a, b] of con.lines) {
          const pa = con.points[a];
          const pb = con.points[b];
          if (!pa || !pb || pa.alt <= 0 || pb.alt <= 0) continue;
          const p1 = project(pa.alt, pa.az, radius);
          const p2 = project(pb.alt, pb.az, radius);
          ctx.beginPath();
          ctx.moveTo(cx + p1.x, cy + p1.y);
          ctx.lineTo(cx + p2.x, cy + p2.y);
          ctx.stroke();
        }
        // 이름: 지평선 위 별들의 중심에 라벨
        const vis = con.points.filter((p) => p.alt > 0);
        if (vis.length) {
          let sx = 0;
          let sy = 0;
          for (const p of vis) {
            const pr = project(p.alt, p.az, radius);
            sx += pr.x;
            sy += pr.y;
          }
          sx /= vis.length;
          sy /= vis.length;
          ctx.fillStyle = "rgba(140,170,220,0.7)";
          ctx.fillText(con.name_ko, cx + sx, cy + sy);
        }
      }
    }

    // 별 그리기 (밝은 것부터, 밝은 별은 이름 라벨)
    const sorted = [...stars].sort((a, b) => a.mag - b.mag);
    for (const s of sorted) {
      const { x, y } = project(s.alt, s.az, radius);
      const px = cx + x;
      const py = cy + y;
      const r = starRadius(s.mag);
      ctx.beginPath();
      ctx.arc(px, py, r, 0, Math.PI * 2);
      ctx.fillStyle = "#eef3ff";
      ctx.shadowColor = "rgba(180,210,255,0.8)";
      ctx.shadowBlur = r * 1.5;
      ctx.fill();
      ctx.shadowBlur = 0;
    }
    // 아주 밝은 별(≤1.0등급)만 이름 표시
    ctx.fillStyle = "rgba(200,215,245,0.85)";
    ctx.font = "10px sans-serif";
    ctx.textAlign = "left";
    for (const s of sorted.filter((x) => x.mag <= 1.0)) {
      const { x, y } = project(s.alt, s.az, radius);
      ctx.fillText(s.name, cx + x + 5, cy + y);
    }
  }, [stars, constellations, showConstellations, size]);

  return (
    <canvas
      ref={canvasRef}
      style={{ width: size, height: size, borderRadius: "50%" }}
      aria-label="밤하늘 별 지도"
    />
  );
}

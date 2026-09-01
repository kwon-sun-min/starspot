// 점수 -> 색상 매핑 (마커/뱃지 공통).
// 낮음(빨강) -> 중간(노랑) -> 높음(초록/청록) 그라데이션.

export function scoreColor(score: number): string {
  if (score >= 80) return "#22d3ee"; // 아주 좋음 (cyan)
  if (score >= 65) return "#4ade80"; // 좋음 (green)
  if (score >= 50) return "#facc15"; // 보통 (yellow)
  if (score >= 35) return "#fb923c"; // 나쁨 (orange)
  return "#f87171"; // 아주 나쁨 (red)
}

export function scoreLabel(score: number): string {
  if (score >= 80) return "최고";
  if (score >= 65) return "좋음";
  if (score >= 50) return "보통";
  if (score >= 35) return "아쉬움";
  return "나쁨";
}

export const CATEGORY_LABEL: Record<string, string> = {
  observatory: "천문대",
  campsite: "야영장",
  viewpoint: "전망대",
  park: "공원",
};

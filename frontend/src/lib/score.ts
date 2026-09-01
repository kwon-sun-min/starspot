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

// Bortle 등급(1=최상 암흑 ~ 9=도심) -> 관측 맥락 설명.
// 낮은 점수(도심 공원)도 "무엇이 보이는지" 알려줘 기대치를 맞춘다.
export function bortleGuide(bortle: number | null): { title: string; desc: string } {
  if (bortle == null) return { title: "광공해 정보 없음", desc: "관측 여건은 하늘 상태로 판단하세요." };
  if (bortle <= 2)
    return {
      title: "청정 암흑 하늘",
      desc: "은하수가 또렷하게 보이고 수천 개의 별과 성운·성단까지 관측할 수 있어요.",
    };
  if (bortle <= 3)
    return {
      title: "시골 하늘",
      desc: "은하수가 잘 보이고 대부분의 별자리와 밝은 성운을 즐길 수 있어요.",
    };
  if (bortle <= 4)
    return {
      title: "시골–교외 전이",
      desc: "은하수 윤곽이 보이고 주요 별자리와 밝은 별·행성 관측에 좋아요.",
    };
  if (bortle <= 5)
    return {
      title: "교외 하늘",
      desc: "은하수는 희미하지만 밝은 별자리·행성·달은 충분히 즐길 수 있어요.",
    };
  if (bortle <= 6)
    return {
      title: "밝은 교외",
      desc: "은하수는 거의 안 보이지만 달·행성과 1등성급 밝은 별은 잘 보여요.",
    };
  if (bortle <= 7)
    return {
      title: "교외–도심 전이",
      desc: "달·행성과 가장 밝은 별 위주로 관측 가능해요. 별자리 식별은 어려워요.",
    };
  return {
    title: "도심 하늘",
    desc: "광공해가 강해 달·행성과 몇몇 밝은 별만 보여요. 가볍게 밤하늘을 즐기기 좋아요.",
  };
}

// 오늘 밤 점수 -> 추천 문구 (구름/달 등 종합 반영된 점수 해석).
export function scoreAdvice(score: number): string {
  if (score >= 80) return "오늘 밤 관측 최적! 별 보러 나가기 딱 좋아요.";
  if (score >= 65) return "관측하기 좋은 밤이에요. 밝은 곳만 피하면 훌륭해요.";
  if (score >= 50) return "무난한 편이에요. 달·행성과 밝은 별은 볼 만해요.";
  if (score >= 35) return "여건이 아쉬워요. 구름이나 달빛의 영향이 커요.";
  return "오늘 밤은 관측이 어려워요. 다른 날을 노려보세요.";
}

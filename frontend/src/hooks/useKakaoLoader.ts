import { useEffect, useState } from "react";

// 런타임 주입 키. 컨테이너 배포는 index.html 이 로드하는 /env.js 가 window.__ENV__ 를 채운다.
// Vercel 등 정적 배포는 env.js 가 없으므로 Vite 빌드 환경변수(VITE_KAKAO_MAP_KEY)로 대체한다.
declare global {
  interface Window {
    kakao: any;
    __ENV__?: { KAKAO_MAP_KEY?: string; API_BASE?: string };
  }
}

let loadingPromise: Promise<void> | null = null;

function loadSdk(appKey: string): Promise<void> {
  if (window.kakao?.maps) return Promise.resolve();
  if (loadingPromise) return loadingPromise;

  loadingPromise = new Promise<void>((resolve, reject) => {
    const script = document.createElement("script");
    script.src =
      `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${appKey}&autoload=false`;
    script.async = true;
    script.onload = () => window.kakao.maps.load(() => resolve());
    script.onerror = () => reject(new Error("카카오맵 SDK 로드 실패"));
    document.head.appendChild(script);
  });
  return loadingPromise;
}

export function useKakaoLoader(): { ready: boolean; error: string | null } {
  const [ready, setReady] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const key =
      window.__ENV__?.KAKAO_MAP_KEY ||
      (import.meta.env.VITE_KAKAO_MAP_KEY as string | undefined);
    if (!key) {
      setError("카카오맵 키가 설정되지 않았습니다 (KAKAO_MAP_KEY).");
      return;
    }
    loadSdk(key)
      .then(() => setReady(true))
      .catch((e) => setError(String(e.message ?? e)));
  }, []);

  return { ready, error };
}

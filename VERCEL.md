# StarSpot 프론트엔드 Vercel 배포 가이드

Vercel 은 정적 프론트엔드에 최적화된 플랫폼입니다. StarSpot **프론트엔드(React/Vite)** 만
Vercel 에 배포하고, **백엔드(FastAPI + PostGIS + Redis)** 는 Vercel 에 올릴 수 없으므로
별도로 호스팅해야 합니다(로컬 `docker compose up` 또는 Railway/Render 등).

> 백엔드가 떠 있지 않으면 화면(지도·UI)은 뜨지만 후보지/점수 데이터가 나오지 않습니다.

## 사전 준비

- 백엔드가 접근 가능한 URL 을 가지고 있어야 합니다.
  - 예: 로컬 데모면 `http://localhost:8080`(브라우저와 같은 PC),
    공개 배포면 `https://<your-backend-domain>`.
- 백엔드는 프론트 도메인의 요청을 허용하는 **CORS** 설정이 필요합니다(아래 참고).

## 1. Vercel 프로젝트 생성

1. https://vercel.com 로그인 → **Add New → Project** → 이 GitHub 저장소 import.
2. **Root Directory** 를 `frontend` 로 지정.
   - `frontend/vercel.json` 이 빌드(`npm run build`)·출력(`dist`)·SPA rewrite 를 자동 설정합니다.
3. Framework Preset: **Vite** (자동 감지됨).

## 2. 환경변수 (Vercel Project Settings → Environment Variables)

| 변수 | 값 | 설명 |
|------|-----|------|
| `VITE_API_BASE` | `https://<your-backend>` | 백엔드 절대 URL. 코드가 자동으로 `/api/v1` 을 붙입니다. |
| `VITE_KAKAO_MAP_KEY` | 카카오맵 JavaScript 키 | 지도 SDK 로드용 |

> 이 값들은 **빌드 타임**에 번들로 주입됩니다. 값을 바꾸면 재배포가 필요합니다.
> 백엔드 URL 이 아직 없으면 우선 로컬 백엔드로 데모: `VITE_API_BASE=http://localhost:8080`
> (단, 이 경우 접속자 본인 PC 에서 백엔드가 떠 있어야 합니다).

## 3. 카카오맵 도메인 등록

카카오 개발자 콘솔 → 앱 → 플랫폼 → **JavaScript SDK 도메인** 에 Vercel 배포 도메인
(`https://<your-project>.vercel.app`)을 추가하고 저장하세요. 안 하면 지도가 403 으로 안 뜹니다.

## 4. 백엔드 CORS

프론트(Vercel 도메인)에서 백엔드를 직접 호출하므로, 백엔드가 해당 오리진을 허용해야 합니다.
로컬 compose 처럼 nginx 프록시를 쓰면 동일 오리진이라 CORS 가 필요 없지만, Vercel 분리 배포에서는
백엔드에 `CORSMiddleware` 로 `https://<your-project>.vercel.app` 오리진 허용을 추가해야 합니다.

> 현재 백엔드에는 CORS 미들웨어가 없습니다. Vercel + 원격 백엔드로 완전 공개하려면
> 백엔드에 CORS 허용을 추가해야 합니다(요청 주시면 붙여드립니다). 로컬 nginx 프록시 데모는 불필요.

## 5. 로컬(compose) 는 그대로

이 변경은 로컬 개발에 영향이 없습니다. `VITE_API_BASE` 를 주지 않으면 프론트는 상대경로
`/api/v1` 을 쓰고, nginx 가 백엔드로 프록시합니다. `docker compose up` 그대로 동작합니다.

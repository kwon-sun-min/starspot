# StarSpot 배포 가이드 (Railway)

StarSpot 은 5개 구성요소(프론트/API/워커/PostGIS/Redis)로 이루어진 풀스택 앱입니다.
Railway 는 서비스별 컨테이너 + 관리형 Postgres/Redis + private networking 을 지원하므로
현재 구조를 거의 그대로 배포할 수 있습니다.

> 로컬 개발은 `docker compose up` 을 그대로 쓰면 됩니다. 이 문서는 클라우드 배포용입니다.

## 서비스 구성

| Railway 서비스 | 소스 | 역할 |
|----------------|------|------|
| **postgis** | 템플릿(PostGIS 이미지) | 공간 DB |
| **redis** | Railway Redis 플러그인 | 예보 캐시 |
| **api** | `backend/Dockerfile` | FastAPI |
| **worker** | `backend/Dockerfile` (start 명령만 다름) | 예보 프리페치 |
| **frontend** | `frontend/Dockerfile` (context=repo root) | nginx 정적 + /api 프록시 |

---

## 1. Postgres + PostGIS

Railway 기본 Postgres 플러그인은 PostGIS 확장이 없을 수 있습니다. 아래 중 하나를 사용하세요.

- **권장**: Railway 템플릿 "TimescaleDB + PostGIS" 또는 "PostgreSQL Extensions"(배포 시 PostGIS 활성화) 배포.
- 배포 후 Variables 에서 `DATABASE_URL`(또는 개별 PG 변수)을 확인합니다.

> 앱은 `postgresql+psycopg://...` 형식을 씁니다. Railway 가 주는 `DATABASE_URL` 이
> `postgresql://...` 형식이면 `postgresql+psycopg://...` 로 스킴만 바꿔 `api`/`worker` 에 넣으세요.

## 2. Redis

Railway 대시보드에서 **New → Database → Redis** 추가. 생성되면 `REDIS_URL` 을 참조로 얻습니다.

## 3. API 서비스

- **New → GitHub Repo** 로 이 저장소 연결.
- Settings → **Root Directory**: `backend`
- 빌드: Dockerfile (레포의 `backend/railway.json` 이 자동 적용) — 마이그레이션+시드+uvicorn 을 시작 시 실행하고 `$PORT` 로 바인딩합니다.
- **Networking**: Public Domain 은 필요 없음(프론트가 내부로 프록시). 내부 도메인 `api.railway.internal` 사용.
- 환경변수:

  | 변수 | 값 |
  |------|-----|
  | `DATABASE_URL` | postgis 서비스 참조 (스킴 `postgresql+psycopg://`) |
  | `REDIS_URL` | redis 서비스 참조 |
  | `KMA_SERVICE_KEY` | 기상청 키 (Decoding) |
  | `TZ` | `Asia/Seoul` |
  | `LOG_LEVEL` | `INFO` |
  | `PYTHONPATH` | `/app` |

## 4. Worker 서비스

- 같은 저장소 + **Root Directory `backend`** 로 서비스 하나 더 추가.
- Settings → Deploy → **Custom Start Command**:
  ```
  python -m app.workers.refresh
  ```
- 환경변수는 API 와 동일(`DATABASE_URL`/`REDIS_URL`/`KMA_SERVICE_KEY`/`TZ`/`PYTHONPATH`).
- 헬스체크 없음(HTTP 서버 아님).

> 대안: 워커 대신 Railway **Cron** 을 써도 됩니다. 발표시각(02/05/08/11/14/17/20/23시)+15분에
> `python -c "import asyncio; from app.workers.refresh import prefetch_all; asyncio.run(prefetch_all())"` 실행.

## 5. Frontend (nginx) 서비스

- 같은 저장소 연결, **Root Directory 는 레포 루트**(프론트 Dockerfile 이 `frontend/`, `infra/` 를 함께 참조).
  - `frontend/railway.json` 에 `dockerfilePath: frontend/Dockerfile` 지정됨.
- Networking → **Generate Domain** 으로 공개 도메인 발급 (사용자 접속점).
- 환경변수:

  | 변수 | 값 |
  |------|-----|
  | `API_UPSTREAM` | `http://api.railway.internal:8000` (api 서비스 내부 주소) |
  | `KAKAO_MAP_KEY` | 카카오맵 JavaScript 키 |

  > nginx 는 시작 시 `API_UPSTREAM`/`PORT` 로 설정을 렌더링하고, `KAKAO_MAP_KEY` 를 `env.js` 로 주입합니다(이미지 재빌드 불필요).

## 6. 카카오맵 도메인 등록

카카오 개발자 콘솔 → 앱 → 플랫폼 → **JavaScript SDK 도메인** 에 Railway 프론트 공개 도메인
(`https://<your-frontend>.up.railway.app`)을 추가하고 저장하세요. 안 하면 지도가 403 으로 안 뜹니다.

## 7. 배포 순서

1. postgis, redis 먼저 생성 → 접속 변수 확인
2. api 생성 (DATABASE_URL/REDIS_URL 등 주입) → 시작 시 자동 migrate+seed
3. worker 생성 (start command 변경)
4. frontend 생성 (`API_UPSTREAM`, `KAKAO_MAP_KEY`) → 공개 도메인 발급
5. 카카오 콘솔에 프론트 도메인 등록
6. 프론트 도메인 접속 → 위치 허용 → 랭킹/지도 확인

## 시크릿 주의

`.env` 와 실제 키는 **커밋 금지**(이미 `.gitignore` 처리). Railway 환경변수로만 주입합니다.
`KMA_SERVICE_KEY`, `KAKAO_MAP_KEY` 는 발급받은 값을 각 서비스 Variables 에 직접 넣으세요.

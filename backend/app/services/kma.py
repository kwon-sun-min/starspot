"""기상청 단기예보(getVilageFcst) 클라이언트.

핵심 책임:
1. 현재 시각(KST) -> 가장 최근 발표분 base_date/base_time 계산.
   발표 시각: 02/05/08/11/14/17/20/23시. 발표 후 약 10분 지연을 고려한다.
2. httpx 비동기 클라이언트로 예보 조회 (타임아웃 5초, 지수 백오프 3회 재시도).
3. 응답의 시간대별 SKY(하늘상태)/PTY(강수형태)를 파싱.

주의: 이 모듈은 네트워크 호출만 담당한다. 캐시 경유는 fetch_forecast 에서 강제한다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import get_settings
from app.services import cache

KST = ZoneInfo("Asia/Seoul")

# 기상청 단기예보 발표 시각(시)
_BASE_HOURS = [2, 5, 8, 11, 14, 17, 20, 23]
# 발표 후 자료 생성 지연(분)
_PUBLISH_DELAY_MIN = 10

_ENDPOINT = (
    "https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
)


@dataclass(frozen=True)
class BaseTime:
    base_date: str  # YYYYMMDD
    base_time: str  # HHMM (예: "2300")


@dataclass
class HourForecast:
    """특정 예보시각(KST)의 하늘/강수 상태."""

    dt: datetime
    sky: int | None = None  # 1 맑음 / 3 구름많음 / 4 흐림
    pty: int | None = None  # 0 없음 / 1 비 / 2 비눈 / 3 눈 / 4 소나기 ...


@dataclass
class ForecastBundle:
    base: BaseTime
    hours: dict[str, HourForecast] = field(default_factory=dict)  # key: YYYYMMDDHHMM

    def to_dict(self) -> dict:
        return {
            "base_date": self.base.base_date,
            "base_time": self.base.base_time,
            "hours": {
                k: {"dt": h.dt.isoformat(), "sky": h.sky, "pty": h.pty}
                for k, h in self.hours.items()
            },
        }

    @staticmethod
    def from_dict(d: dict) -> ForecastBundle:
        base = BaseTime(base_date=d["base_date"], base_time=d["base_time"])
        hours: dict[str, HourForecast] = {}
        for k, v in d.get("hours", {}).items():
            hours[k] = HourForecast(
                dt=datetime.fromisoformat(v["dt"]),
                sky=v.get("sky"),
                pty=v.get("pty"),
            )
        return ForecastBundle(base=base, hours=hours)


def compute_base_time(now: datetime | None = None) -> BaseTime:
    """현재 시각(KST) 기준 가장 최근 발표분 base_date/base_time 을 계산한다.

    발표 후 _PUBLISH_DELAY_MIN 분이 지나야 해당 발표분을 사용할 수 있다.
    예) 02:07 -> 아직 02시 발표분 미생성 -> 전날 23시 발표분 사용.
        02:11 -> 02시 발표분 사용.
    """
    if now is None:
        now = datetime.now(KST)
    else:
        if now.tzinfo is None:
            raise ValueError("naive datetime 은 허용하지 않습니다.")
        now = now.astimezone(KST)

    # 지연을 뺀 '유효 시각' 기준으로 발표시각을 선택
    effective = now - timedelta(minutes=_PUBLISH_DELAY_MIN)
    eff_hour = effective.hour

    chosen_hour: int | None = None
    for h in reversed(_BASE_HOURS):
        if eff_hour >= h:
            chosen_hour = h
            break

    if chosen_hour is None:
        # 00:00~02:09 구간 -> 전날 23시 발표분
        prev_day = (effective - timedelta(days=1)).date()
        return BaseTime(base_date=prev_day.strftime("%Y%m%d"), base_time="2300")

    return BaseTime(
        base_date=effective.strftime("%Y%m%d"),
        base_time=f"{chosen_hour:02d}00",
    )


class KmaError(Exception):
    pass


@retry(
    retry=retry_if_exception_type((httpx.HTTPError, KmaError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
    reraise=True,
)
async def _request(nx: int, ny: int, base: BaseTime) -> dict:
    settings = get_settings()
    if not settings.kma_service_key:
        raise KmaError("KMA_SERVICE_KEY 가 설정되지 않았습니다.")
    params = {
        "serviceKey": settings.kma_service_key,
        "pageNo": "1",
        "numOfRows": "1000",
        "dataType": "JSON",
        "base_date": base.base_date,
        "base_time": base.base_time,
        "nx": str(nx),
        "ny": str(ny),
    }
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(_ENDPOINT, params=params)
        resp.raise_for_status()
        data = resp.json()
    header = (
        data.get("response", {}).get("header", {})
    )
    if header.get("resultCode") not in (None, "00"):
        raise KmaError(f"KMA resultCode={header.get('resultCode')} msg={header.get('resultMsg')}")
    return data


def _parse(data: dict, base: BaseTime) -> ForecastBundle:
    bundle = ForecastBundle(base=base)
    items = (
        data.get("response", {})
        .get("body", {})
        .get("items", {})
        .get("item", [])
    )
    for it in items:
        cat = it.get("category")
        if cat not in ("SKY", "PTY"):
            continue
        fdate = it.get("fcstDate")  # YYYYMMDD
        ftime = it.get("fcstTime")  # HHMM
        key = f"{fdate}{ftime}"
        if key not in bundle.hours:
            dt = datetime.strptime(f"{fdate}{ftime}", "%Y%m%d%H%M").replace(tzinfo=KST)
            bundle.hours[key] = HourForecast(dt=dt)
        try:
            val = int(it.get("fcstValue"))
        except (TypeError, ValueError):
            continue
        if cat == "SKY":
            bundle.hours[key].sky = val
        else:
            bundle.hours[key].pty = val
    return bundle


async def fetch_forecast(
    nx: int, ny: int, base: BaseTime | None = None
) -> tuple[ForecastBundle, bool]:
    """캐시 경유 예보 조회. (bundle, stale) 반환.

    1) 캐시 신선본 있으면 반환.
    2) 없으면 기상청 호출 -> 성공 시 캐시에 저장 후 반환.
    3) 기상청 장애 시 stale 백업이 있으면 stale=True 로 반환, 없으면 예외.
    """
    if base is None:
        base = compute_base_time()

    cached = cache.get_forecast(nx, ny, base.base_date, base.base_time)
    if cached.hit and cached.value is not None:
        return ForecastBundle.from_dict(cached.value), False

    try:
        data = await _request(nx, ny, base)
        bundle = _parse(data, base)
        cache.set_forecast(nx, ny, base.base_date, base.base_time, bundle.to_dict())
        _kma_outcome("success")
        return bundle, False
    except (httpx.HTTPError, KmaError):
        _kma_outcome("failure")
        # 장애 fallback: stale 백업이라도 사용
        if cached.stale and cached.value is not None:
            return ForecastBundle.from_dict(cached.value), True
        raise


def _kma_outcome(outcome: str) -> None:
    try:
        from app.observability import KMA_REQUESTS

        KMA_REQUESTS.labels(outcome=outcome).inc()
    except Exception:  # noqa: BLE001
        pass

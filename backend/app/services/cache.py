"""Redis 캐시 래퍼.

- 키 규칙: kma:{nx}:{ny}:{base_date}{base_time}
- TTL: 기본 3시간 (기상청 발표 주기)
- 히트/미스 카운터를 Redis 에 누적 (README 수치용, /metrics/cache 로 노출)
- stale fallback: 정상 캐시(신선본)가 없을 때, 별도 stale 키에 저장해 둔 마지막
  성공본을 반환할 수 있게 한다. 이때 호출측은 stale=True 로 응답해야 한다.

기상청 API 호출은 반드시 이 캐시를 경유한다 (캐시 우회 경로 없음).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import redis

from app.config import get_settings

_settings = get_settings()

# 카운터 키
HIT_KEY = "metrics:cache:hits"
MISS_KEY = "metrics:cache:misses"
STALE_KEY = "metrics:cache:stale_served"

# stale 백업은 신선본 TTL 보다 훨씬 길게 유지 (기상청 장애 대비)
STALE_TTL = 24 * 60 * 60


@dataclass
class CacheResult:
    value: dict[str, Any] | None
    hit: bool
    stale: bool


def _client() -> redis.Redis:
    return redis.Redis.from_url(_settings.redis_url, decode_responses=True)


def forecast_key(nx: int, ny: int, base_date: str, base_time: str) -> str:
    return f"kma:{nx}:{ny}:{base_date}{base_time}"


def _stale_backup_key(nx: int, ny: int) -> str:
    """격자별 마지막 성공 예보 백업 (base_time 무관, 최신 1건 유지)."""
    return f"kma:stale:{nx}:{ny}"


def get_forecast(
    nx: int, ny: int, base_date: str, base_time: str, *, client: redis.Redis | None = None
) -> CacheResult:
    """캐시에서 예보를 조회. 신선본 없으면 stale 백업을 시도한다."""
    r = client or _client()
    key = forecast_key(nx, ny, base_date, base_time)
    raw = r.get(key)
    if raw is not None:
        r.incr(HIT_KEY)
        _prom("hit")
        return CacheResult(value=json.loads(raw), hit=True, stale=False)

    r.incr(MISS_KEY)
    _prom("miss")
    # 신선본 미스 -> stale 백업 확인
    stale_raw = r.get(_stale_backup_key(nx, ny))
    if stale_raw is not None:
        r.incr(STALE_KEY)
        _prom("stale")
        return CacheResult(value=json.loads(stale_raw), hit=False, stale=True)
    return CacheResult(value=None, hit=False, stale=False)


def _prom(result: str) -> None:
    """Prometheus 카운터 증가 (관측성 모듈이 없어도 캐시는 동작해야 하므로 지연 임포트)."""
    try:
        from app.observability import CACHE_EVENTS

        CACHE_EVENTS.labels(result=result).inc()
    except Exception:  # noqa: BLE001
        pass


def set_forecast(
    nx: int,
    ny: int,
    base_date: str,
    base_time: str,
    value: dict[str, Any],
    *,
    ttl: int | None = None,
    client: redis.Redis | None = None,
) -> None:
    """신선본 + stale 백업을 함께 저장한다."""
    r = client or _client()
    payload = json.dumps(value, ensure_ascii=False)
    r.set(forecast_key(nx, ny, base_date, base_time), payload, ex=ttl or _settings.kma_cache_ttl)
    # stale 백업 갱신 (장애 시 최후의 보루)
    r.set(_stale_backup_key(nx, ny), payload, ex=STALE_TTL)


def metrics(*, client: redis.Redis | None = None) -> dict[str, int]:
    r = client or _client()
    hits = int(r.get(HIT_KEY) or 0)
    misses = int(r.get(MISS_KEY) or 0)
    stale = int(r.get(STALE_KEY) or 0)
    total = hits + misses
    hit_rate = round(hits / total * 100, 2) if total else 0.0
    return {
        "hits": hits,
        "misses": misses,
        "stale_served": stale,
        "total": total,
        "hit_rate_pct": hit_rate,
    }

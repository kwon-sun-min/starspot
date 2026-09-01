"""Redis 캐시 래퍼 단위 테스트 (fakeredis 사용)."""

from __future__ import annotations

import pytest

fakeredis = pytest.importorskip("fakeredis")

from app.services import cache  # noqa: E402


@pytest.fixture
def r():
    return fakeredis.FakeRedis(decode_responses=True)


SAMPLE = {"base_date": "20260902", "base_time": "2300", "hours": {}}


def test_miss_then_set_then_hit(r):
    res = cache.get_forecast(60, 127, "20260902", "2300", client=r)
    assert res.hit is False and res.stale is False and res.value is None

    cache.set_forecast(60, 127, "20260902", "2300", SAMPLE, client=r)

    res2 = cache.get_forecast(60, 127, "20260902", "2300", client=r)
    assert res2.hit is True and res2.stale is False
    assert res2.value == SAMPLE


def test_counters_accumulate(r):
    cache.get_forecast(1, 1, "20260902", "2300", client=r)   # miss
    cache.set_forecast(1, 1, "20260902", "2300", SAMPLE, client=r)
    cache.get_forecast(1, 1, "20260902", "2300", client=r)   # hit
    cache.get_forecast(1, 1, "20260902", "2300", client=r)   # hit

    m = cache.metrics(client=r)
    assert m["hits"] == 2
    assert m["misses"] == 1
    assert m["total"] == 3
    assert m["hit_rate_pct"] == round(2 / 3 * 100, 2)


def test_stale_fallback(r):
    # 어제 발표분을 저장 -> stale 백업이 생성됨
    cache.set_forecast(5, 5, "20260901", "2300", SAMPLE, client=r)
    # 오늘의 다른 base_time 을 조회하면 신선본은 미스지만 stale 백업 히트
    res = cache.get_forecast(5, 5, "20260902", "2300", client=r)
    assert res.hit is False
    assert res.stale is True
    assert res.value == SAMPLE

    m = cache.metrics(client=r)
    assert m["stale_served"] == 1

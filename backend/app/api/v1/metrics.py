"""캐시 메트릭 라우터 (README 수치용)."""

from __future__ import annotations

from fastapi import APIRouter

from app.services import cache

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/cache")
def cache_metrics() -> dict[str, int | float]:
    """기상청 캐시 히트/미스/히트율 누적치."""
    return cache.metrics()

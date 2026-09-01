"""후보지 관련 라우터.

Phase 3: 반경 검색 + darkness/access + 기상청 cloud + 달 방해도 moon 을 조립한 점수.
기상청 호출은 반드시 캐시(services.cache)를 경유한다. 같은 격자를 공유하는 후보지는
격자별로 한 번만 예보를 조회해 호출을 절감한다.

ST_DWithin(geography) 는 미터 단위이므로 radius_km*1000 을 사용한다.
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.spot import (
    Breakdown,
    ForecastResponse,
    HourlyScore,
    SpotDetail,
    SpotSummary,
)
from app.services import assemble, scoring
from app.services.kma import ForecastBundle, compute_base_time, fetch_forecast

router = APIRouter(prefix="/spots", tags=["spots"])
KST = ZoneInfo("Asia/Seoul")


_SEARCH_SQL = text(
    """
    SELECT
        id, name, category, address, elevation_m, radiance,
        darkness_score, bortle, kma_nx, kma_ny,
        ST_Y(geom::geometry) AS lat,
        ST_X(geom::geometry) AS lon,
        ST_Distance(geom, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography) AS dist_m
    FROM spots
    WHERE ST_DWithin(
        geom,
        ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
        :radius_m
    )
    ORDER BY dist_m ASC
    LIMIT :limit
    """
)


async def _forecast_for_grid(
    nx: int, ny: int, cache_grids: dict[tuple[int, int], ForecastBundle | None]
) -> ForecastBundle | None:
    """격자별 예보를 1회만 조회해 재사용. 장애 시 None 으로 폴백(맑음 가정)."""
    key = (nx, ny)
    if key in cache_grids:
        return cache_grids[key]
    try:
        bundle, _stale = await fetch_forecast(nx, ny)
    except Exception:
        bundle = None
    cache_grids[key] = bundle
    return bundle


@router.get("", response_model=list[SpotSummary])
async def list_spots(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(100.0, gt=0, le=500),
    limit: int = Query(50, gt=0, le=300),
    db: Session = Depends(get_db),
) -> list[SpotSummary]:
    rows = (
        db.execute(
            _SEARCH_SQL,
            {"lat": lat, "lon": lon, "radius_m": radius_km * 1000.0, "limit": limit},
        )
        .mappings()
        .all()
    )

    now = datetime.now(KST)
    grid_cache: dict[tuple[int, int], ForecastBundle | None] = {}
    results: list[SpotSummary] = []

    for r in rows:
        distance_km = round(r["dist_m"] / 1000.0, 1)
        darkness = (
            r["darkness_score"]
            if r["darkness_score"] is not None
            else scoring.darkness_from_radiance(r["radiance"])
        )
        bundle = await _forecast_for_grid(r["kma_nx"], r["kma_ny"], grid_cache)
        assembled = assemble.assemble(
            lat=r["lat"],
            lon=r["lon"],
            date=now,
            darkness=darkness,
            distance_km=distance_km,
            bundle=bundle,
        )
        bd = assembled.breakdown
        results.append(
            SpotSummary(
                id=r["id"],
                name=r["name"],
                category=r["category"],
                lat=round(r["lat"], 6),
                lon=round(r["lon"], 6),
                distance_km=distance_km,
                score=assembled.best_score,
                breakdown=Breakdown(**bd.__dict__)
                if bd
                else Breakdown(
                    darkness=darkness,
                    cloud=0,
                    moon=100,
                    access=scoring.access_from_distance(distance_km),
                ),
                bortle=r["bortle"],
                best_hour=assembled.best_hour,
            )
        )

    results.sort(key=lambda s: (-s.score, s.distance_km))
    return results


@router.get("/{spot_id}", response_model=SpotDetail)
def get_spot(spot_id: int, db: Session = Depends(get_db)) -> SpotDetail:
    row = (
        db.execute(
            text(
                """
                SELECT id, name, category, address, elevation_m, radiance,
                       darkness_score, bortle,
                       ST_Y(geom::geometry) AS lat, ST_X(geom::geometry) AS lon
                FROM spots WHERE id = :id
                """
            ),
            {"id": spot_id},
        )
        .mappings()
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="spot not found")
    return SpotDetail(
        id=row["id"],
        name=row["name"],
        category=row["category"],
        address=row["address"],
        lat=round(row["lat"], 6),
        lon=round(row["lon"], 6),
        elevation_m=row["elevation_m"],
        radiance=row["radiance"],
        darkness_score=row["darkness_score"],
        bortle=row["bortle"],
    )


@router.get("/{spot_id}/forecast", response_model=ForecastResponse)
async def get_forecast(
    spot_id: int,
    date: str | None = Query(None, description="YYYY-MM-DD (KST). 미지정 시 오늘."),
    db: Session = Depends(get_db),
) -> ForecastResponse:
    row = (
        db.execute(
            text(
                """
                SELECT id, radiance, darkness_score, kma_nx, kma_ny,
                       ST_Y(geom::geometry) AS lat, ST_X(geom::geometry) AS lon
                FROM spots WHERE id = :id
                """
            ),
            {"id": spot_id},
        )
        .mappings()
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="spot not found")

    if date:
        d = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=KST)
    else:
        d = datetime.now(KST)

    darkness = (
        row["darkness_score"]
        if row["darkness_score"] is not None
        else scoring.darkness_from_radiance(row["radiance"])
    )

    stale = False
    bundle: ForecastBundle | None = None
    try:
        bundle, stale = await fetch_forecast(row["kma_nx"], row["kma_ny"], compute_base_time())
    except Exception:
        bundle = None  # 맑음 가정 폴백

    # 상세는 사용자 거리 정보가 없으므로 access 는 100(현지 기준) 가정
    assembled = assemble.assemble(
        lat=row["lat"],
        lon=row["lon"],
        date=d,
        darkness=darkness,
        distance_km=0.0,
        bundle=bundle,
    )

    return ForecastResponse(
        spot_id=spot_id,
        date=d.strftime("%Y-%m-%d"),
        hourly=[
            HourlyScore(hour=p.hour, score=p.score, cloud=p.cloud, moon=p.moon)
            for p in assembled.hourly
        ],
        best_hour=assembled.best_hour,
        best_score=assembled.best_score,
        stale=stale,
    )

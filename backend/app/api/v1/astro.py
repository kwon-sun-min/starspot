"""천문 정보 라우터: 일출몰·월출몰·월령."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Query

from app.schemas.spot import AstroResponse
from app.services import astro

router = APIRouter(prefix="/astro", tags=["astro"])
KST = ZoneInfo("Asia/Seoul")


@router.get("", response_model=AstroResponse)
def get_astro(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    date: str | None = Query(None, description="YYYY-MM-DD (KST). 미지정 시 오늘."),
) -> AstroResponse:
    if date:
        d = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=KST)
    else:
        d = datetime.now(KST)
    info = astro.astro_info(lat, lon, d)
    return AstroResponse(
        sunset=info.sunset,
        sunrise=info.sunrise,
        moonrise=info.moonrise,
        moonset=info.moonset,
        moon_phase_deg=info.moon_phase_deg,
        moon_illumination=info.moon_illumination,
    )

"""최종 점수 조립.

야간 관측 구간(일몰+1h ~ 일출-1h)을 1시간 단위로 순회하며 각 시각의 점수를 계산하고,
그 구간 최댓값을 '오늘 밤 점수'로 삼는다. 시간대별 배열도 함께 반환한다.

darkness: 후보지 사전계산값(또는 radiance 유도)
cloud   : 해당 시각의 기상청 SKY/PTY -> 0~100
moon    : 해당 시각 달 방해도의 역수 (밤 전체 조도지수 기반, 명세에 따라 하룻밤 단일값)
access  : 사용자 거리 기반 (하룻밤 고정)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.services import astro, scoring
from app.services.kma import ForecastBundle


@dataclass
class HourlyPoint:
    hour: datetime
    score: int
    cloud: int
    moon: int


@dataclass
class AssembledScore:
    hourly: list[HourlyPoint]
    best_hour: datetime | None
    best_score: int
    breakdown: scoring.Breakdown | None


def _cloud_for_hour(bundle: ForecastBundle | None, hour: datetime) -> int:
    """해당 시각(정시)의 기상청 예보로 cloud 산출. 없으면 0(맑음 가정)."""
    if bundle is None:
        return 0
    key = hour.strftime("%Y%m%d%H%M")
    hf = bundle.hours.get(key)
    if hf is None:
        # 정시 예보가 없으면 같은 날짜 근접 시각 탐색은 생략하고 맑음 가정
        return 0
    return scoring.cloud_from_kma(hf.sky, hf.pty)


def assemble(
    lat: float,
    lon: float,
    date: datetime,
    darkness: int,
    distance_km: float,
    bundle: ForecastBundle | None,
) -> AssembledScore:
    win = astro.night_window(lat, lon, date)
    access = scoring.access_from_distance(distance_km)

    # moon 은 명세상 하룻밤 단일값 (조도지수 기반)
    interference = astro.moon_interference(lat, lon, date)
    moon = scoring.moon_from_interference(interference)

    if win is None or not win.hours:
        # 백야/극야 등 야간구간 없음 -> cloud 미반영 단일 점수
        score, bd = scoring.compute_score(darkness, 0, moon, access)
        return AssembledScore(hourly=[], best_hour=None, best_score=score, breakdown=bd)

    hourly: list[HourlyPoint] = []
    best_score = -1
    best_hour: datetime | None = None
    best_bd: scoring.Breakdown | None = None

    for h in win.hours:
        cloud = _cloud_for_hour(bundle, h)
        s, bd = scoring.compute_score(darkness, cloud, moon, access)
        hourly.append(HourlyPoint(hour=h, score=s, cloud=cloud, moon=moon))
        if s > best_score:
            best_score = s
            best_hour = h
            best_bd = bd

    return AssembledScore(
        hourly=hourly,
        best_hour=best_hour,
        best_score=best_score,
        breakdown=best_bd,
    )

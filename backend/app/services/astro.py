"""천문 계산 서비스 (astronomy-engine 기반).

제공:
- 일몰/일출 시각 (관측 야간 구간 산출용)
- 월출/월몰 시각, 월령(위상), 달 밝기(illumination 0~1)
- 관측 시간대(일몰 후 1h ~ 일출 전 1h)의 시간 단위 슬롯 생성
- moon 방해도 계산: 달 밝기 × 관측시간대 중 달이 지평선 위인 비율

모든 datetime 은 타임존 인식(Asia/Seoul). naive datetime 을 반환하지 않는다.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import astronomy as ast

KST = ZoneInfo("Asia/Seoul")
_UTC = ZoneInfo("UTC")


def _require_aware(dt: datetime) -> datetime:
    """naive datetime 을 거부한다 (Asia/Seoul 인식 강제)."""
    if dt.tzinfo is None:
        raise ValueError("naive datetime 은 허용하지 않습니다 (tz-aware 필요).")
    return dt


def _to_time(dt: datetime) -> ast.Time:
    """tz-aware datetime -> astronomy Time (UTC 기준)."""
    if dt.tzinfo is None:
        raise ValueError("naive datetime 은 허용하지 않습니다 (Asia/Seoul 인식 필요).")
    u = dt.astimezone(_UTC)
    return ast.Time.Make(u.year, u.month, u.day, u.hour, u.minute, u.second + u.microsecond / 1e6)


def _to_dt(t: ast.Time | None) -> datetime | None:
    """astronomy Time -> KST datetime."""
    if t is None:
        return None
    y, mo, d, h, mi, s = _calendar(t)
    dt = datetime(y, mo, d, h, mi, int(s), tzinfo=_UTC)
    return dt.astimezone(KST)


def _calendar(t: ast.Time) -> tuple[int, int, int, int, int, float]:
    """astronomy Time 을 UTC 달력 요소로 분해."""
    # astronomy-engine 은 str(Time) 이 ISO8601(UTC) 를 반환한다: 2026-09-02T15:04:05.000Z
    iso = str(t)
    date_part, time_part = iso.rstrip("Z").split("T")
    y, mo, d = (int(x) for x in date_part.split("-"))
    hh, mm, ss = time_part.split(":")
    return y, mo, d, int(hh), int(mm), float(ss)


@dataclass(frozen=True)
class NightWindow:
    sunset: datetime
    sunrise: datetime  # 다음날 일출
    start: datetime     # 일몰 + 1h
    end: datetime       # 일출 - 1h
    hours: list[datetime]  # start~end 1시간 슬롯


@dataclass(frozen=True)
class AstroInfo:
    sunset: datetime | None
    sunrise: datetime | None
    moonrise: datetime | None
    moonset: datetime | None
    moon_phase_deg: float      # 0=신월, 90=상현, 180=보름, 270=하현
    moon_illumination: float   # 0~1 (달 밝은 면 비율)


def sun_events(lat: float, lon: float, date: datetime) -> tuple[datetime | None, datetime | None]:
    """주어진 날짜(KST)의 일몰과 다음 일출을 반환."""
    obs = ast.Observer(lat, lon, 0.0)
    # 정오(KST)를 검색 기준점으로 삼아 그날 저녁 일몰을 찾는다.
    noon = _require_aware(date).astimezone(KST).replace(hour=12, minute=0, second=0, microsecond=0)
    t0 = _to_time(noon)
    sunset_t = ast.SearchRiseSet(ast.Body.Sun, obs, ast.Direction.Set, t0, 1)
    sunrise_t = ast.SearchRiseSet(ast.Body.Sun, obs, ast.Direction.Rise, t0, 2)
    return _to_dt(sunset_t), _to_dt(sunrise_t)


def moon_events(lat: float, lon: float, date: datetime) -> tuple[datetime | None, datetime | None]:
    obs = ast.Observer(lat, lon, 0.0)
    noon = _require_aware(date).astimezone(KST).replace(hour=12, minute=0, second=0, microsecond=0)
    t0 = _to_time(noon)
    rise_t = ast.SearchRiseSet(ast.Body.Moon, obs, ast.Direction.Rise, t0, 2)
    set_t = ast.SearchRiseSet(ast.Body.Moon, obs, ast.Direction.Set, t0, 2)
    return _to_dt(rise_t), _to_dt(set_t)


def moon_phase_and_illumination(date: datetime) -> tuple[float, float]:
    """월령(0~360도)과 밝은 면 비율(0~1)."""
    noon = _require_aware(date).astimezone(KST).replace(hour=21, minute=0, second=0, microsecond=0)
    t = _to_time(noon)
    phase = ast.MoonPhase(t)  # 0~360 deg
    illum = ast.Illumination(ast.Body.Moon, t)
    return float(phase), float(illum.phase_fraction)


def astro_info(lat: float, lon: float, date: datetime) -> AstroInfo:
    sunset, sunrise = sun_events(lat, lon, date)
    moonrise, moonset = moon_events(lat, lon, date)
    phase, illum = moon_phase_and_illumination(date)
    return AstroInfo(
        sunset=sunset,
        sunrise=sunrise,
        moonrise=moonrise,
        moonset=moonset,
        moon_phase_deg=phase,
        moon_illumination=illum,
    )


def night_window(lat: float, lon: float, date: datetime) -> NightWindow | None:
    """관측 야간 구간: 일몰+1h ~ 일출-1h, 1시간 슬롯 리스트."""
    sunset, sunrise = sun_events(lat, lon, date)
    if sunset is None or sunrise is None:
        return None
    start = (sunset + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    end = (sunrise - timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    hours: list[datetime] = []
    cur = start
    while cur <= end:
        hours.append(cur)
        cur += timedelta(hours=1)
    return NightWindow(sunset=sunset, sunrise=sunrise, start=start, end=end, hours=hours)


def moon_altitude_deg(lat: float, lon: float, when: datetime) -> float:
    """주어진 시각에 달의 지평선 고도(도). 음수면 지평선 아래."""
    obs = ast.Observer(lat, lon, 0.0)
    t = _to_time(_require_aware(when))
    equ = ast.Equator(ast.Body.Moon, t, obs, True, True)
    hor = ast.Horizon(t, obs, equ.ra, equ.dec, ast.Refraction.Normal)
    return float(hor.altitude)


def moon_interference(lat: float, lon: float, date: datetime) -> float:
    """달 방해도(0~100). 조도지수 = 밝기(0~1) × 달이 지평선 위인 시간 비율(0~1) × 100.

    명세: moon = 100 - 조도지수.  이 함수는 조도지수를 반환한다.
    """
    win = night_window(lat, lon, date)
    _, illum = moon_phase_and_illumination(date)
    if win is None or not win.hours:
        return illum * 100.0
    above = sum(1 for h in win.hours if moon_altitude_deg(lat, lon, h) > 0.0)
    frac_above = above / len(win.hours)
    return illum * frac_above * 100.0

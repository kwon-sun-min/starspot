"""기상청 단기예보 격자 <-> 위경도 변환.

기상청 동네예보는 Lambert Conformal Conic (LCC) 투영 기반의 5km 격자를 사용한다.
아래 상수와 알고리즘은 기상청이 배포하는 공식 예제(dfs_xy_conv)를 파이썬으로 옮긴 것이다.

기준 격자: 전국을 149(가로) x 253(세로) 격자로 나눈다. (1,1)은 좌하단이 아니라
좌상단 기준이며, 서울(37.5714, 126.9658)이 (60, 127)에 대응하는 것으로 검증한다.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# ---- 기상청 공식 LCC 파라미터 ----
_RE = 6371.00877          # 지구 반경 (km)
_GRID = 5.0               # 격자 간격 (km)
_SLAT1 = 30.0             # 표준 위도 1 (deg)
_SLAT2 = 60.0             # 표준 위도 2 (deg)
_OLON = 126.0            # 기준점 경도 (deg)
_OLAT = 38.0             # 기준점 위도 (deg)
_XO = 43                  # 기준점 X 좌표 (격자)
_YO = 136                 # 기준점 Y 좌표 (격자)

_DEGRAD = math.pi / 180.0
_RADDEG = 180.0 / math.pi


@dataclass(frozen=True)
class Grid:
    nx: int
    ny: int


def _lcc_constants() -> tuple[float, float, float, float]:
    """LCC 투영에 필요한 파생 상수(re, sn, sf, ro)를 계산한다."""
    re = _RE / _GRID
    slat1 = _SLAT1 * _DEGRAD
    slat2 = _SLAT2 * _DEGRAD
    olat = _OLAT * _DEGRAD

    sn = math.tan(math.pi * 0.25 + slat2 * 0.5) / math.tan(math.pi * 0.25 + slat1 * 0.5)
    sn = math.log(math.cos(slat1) / math.cos(slat2)) / math.log(sn)

    sf = math.tan(math.pi * 0.25 + slat1 * 0.5)
    sf = (sf**sn) * math.cos(slat1) / sn

    ro = math.tan(math.pi * 0.25 + olat * 0.5)
    ro = re * sf / (ro**sn)
    return re, sn, sf, ro


def latlon_to_grid(lat: float, lon: float) -> Grid:
    """위경도(도) -> 기상청 격자 (nx, ny). 반올림하여 정수 격자로 반환한다."""
    re, sn, sf, ro = _lcc_constants()

    ra = math.tan(math.pi * 0.25 + (lat * _DEGRAD) * 0.5)
    ra = re * sf / (ra**sn)

    theta = lon * _DEGRAD - _OLON * _DEGRAD
    if theta > math.pi:
        theta -= 2.0 * math.pi
    if theta < -math.pi:
        theta += 2.0 * math.pi
    theta *= sn

    nx = int(math.floor(ra * math.sin(theta) + _XO + 0.5))
    ny = int(math.floor(ro - ra * math.cos(theta) + _YO + 0.5))
    return Grid(nx=nx, ny=ny)


def grid_to_latlon(nx: int, ny: int) -> tuple[float, float]:
    """기상청 격자 (nx, ny) -> 격자 중심의 위경도(도)."""
    re, sn, sf, ro = _lcc_constants()

    xn = nx - _XO
    yn = ro - ny + _YO
    ra = math.sqrt(xn * xn + yn * yn)
    if sn < 0.0:
        ra = -ra
    alat = (re * sf / ra) ** (1.0 / sn)
    alat = 2.0 * math.atan(alat) - math.pi * 0.5

    if abs(xn) <= 0.0:
        theta = 0.0
    elif abs(yn) <= 0.0:
        theta = math.pi * 0.5
        if xn < 0.0:
            theta = -theta
    else:
        theta = math.atan2(xn, yn)

    alon = theta / sn + _OLON * _DEGRAD
    return alat * _RADDEG, alon * _RADDEG

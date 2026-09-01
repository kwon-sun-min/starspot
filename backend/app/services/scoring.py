"""관측 점수 계산.

score = 0.40*darkness + 0.35*(100-cloud) + 0.15*moon + 0.10*access

각 항목은 0~100 스케일. 이 모듈은 순수 함수만 가지며 외부 I/O 가 없어 단위 테스트하기 쉽다.
Phase 2 에서는 cloud(기상청)가 아직 없으므로 cloud=0(=맑음 가정)으로 두고
darkness/access 중심의 점수를 산출한다. Phase 3 에서 cloud/moon 실측을 주입한다.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# 기본(darkness) 모드 가중치. 관측 품질을 우선하되 접근성을 이전(0.10)보다 반영한다.
W_DARKNESS = 0.35
W_CLOUD = 0.35
W_MOON = 0.10
W_ACCESS = 0.20

# "근처(nearby)" 모드 가중치. 가까움을 크게 우대해 일상적으로 갈 만한 곳을 상위로.
W_NEARBY = {
    "darkness": 0.25,
    "cloud": 0.30,
    "moon": 0.10,
    "access": 0.35,
}

# VIIRS radiance 정규화 범위 (log10(r+0.1) 압축 후 이 구간을 0~100 에 매핑)
# r=0(완전 암흑) -> log10(0.1) = -1.0,  r≈250(도심) -> log10(250.1) ≈ 2.4
_LOG_MIN = -1.0
_LOG_MAX = 2.4


@dataclass(frozen=True)
class Breakdown:
    darkness: int
    cloud: int
    moon: int
    access: int


def darkness_from_radiance(radiance: float | None) -> int:
    """VIIRS radiance(nW/cm²/sr) -> darkness 점수 0~100. 값이 낮을수록(어두울수록) 높다."""
    if radiance is None:
        return 50  # 미측정 시 중립값
    r = max(0.0, radiance)
    compressed = math.log10(r + 0.1)
    # 0~1 정규화
    norm = (compressed - _LOG_MIN) / (_LOG_MAX - _LOG_MIN)
    norm = min(1.0, max(0.0, norm))
    # 반전: 어두울수록(작은 radiance) 높은 점수
    return round((1.0 - norm) * 100)


def access_from_distance(distance_km: float) -> int:
    """접근성 점수(0~100). 거리 감쇠를 완만하게: 100 - d*0.5.

    이전(100 - d)은 100km 밖이 곧바로 0점이라 조금만 멀어도 접근성이 급락했다.
    완만한 감쇠로 바꿔 100km도 50점을 주어, '가깝고 그럭저럭 어두운' 일상 관측지가
    순위에 올라올 수 있게 한다.
    """
    return int(max(0.0, 100.0 - distance_km * 0.5))


def cloud_from_kma(sky: int | None, pty: int | None) -> int:
    """기상청 SKY(1/3/4) -> 0/60/100. PTY(강수형태)가 0이 아니면 100 강제."""
    if pty is not None and pty != 0:
        return 100
    mapping = {1: 0, 3: 60, 4: 100}
    if sky is None:
        return 0
    return mapping.get(sky, 0)


def moon_from_interference(interference_index: float) -> int:
    """moon = 100 - 조도지수. 조도지수는 0~100."""
    return int(round(100.0 - min(100.0, max(0.0, interference_index))))


def compute_score(
    darkness: int,
    cloud: int,
    moon: int,
    access: int,
    mode: str = "darkness",
) -> tuple[int, Breakdown]:
    """가중합으로 최종 점수(0~100)와 분해 항목을 반환.

    mode="darkness"(기본): 관측 품질 우선.
    mode="nearby": 접근성을 크게 우대(일상적으로 갈 만한 곳 상위).
    """
    d = _clamp(darkness)
    c = _clamp(cloud)
    m = _clamp(moon)
    a = _clamp(access)
    if mode == "nearby":
        w = W_NEARBY
        raw = w["darkness"] * d + w["cloud"] * (100 - c) + w["moon"] * m + w["access"] * a
    else:
        raw = W_DARKNESS * d + W_CLOUD * (100 - c) + W_MOON * m + W_ACCESS * a
    return round(raw), Breakdown(darkness=d, cloud=c, moon=m, access=a)


def _clamp(v: int) -> int:
    return int(min(100, max(0, v)))

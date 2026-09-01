"""점수 계산 단위 테스트."""

from __future__ import annotations

import pytest

from app.services import scoring


def test_darkness_dark_site_high_score():
    """radiance 가 아주 낮으면(어두우면) darkness 점수가 높아야 한다."""
    assert scoring.darkness_from_radiance(0.0) >= 90


def test_darkness_bright_city_low_score():
    """도심 수준 radiance(≈250)면 darkness 점수가 낮아야 한다."""
    assert scoring.darkness_from_radiance(250.0) <= 10


def test_darkness_monotonic():
    """radiance 가 커질수록 darkness 점수는 단조 감소(비증가)해야 한다."""
    vals = [scoring.darkness_from_radiance(r) for r in [0.1, 1, 5, 20, 80, 200]]
    assert all(a >= b for a, b in zip(vals, vals[1:], strict=False))


def test_darkness_none_neutral():
    assert scoring.darkness_from_radiance(None) == 50


@pytest.mark.parametrize(
    "d,expected",
    [(0, 100), (50, 75), (100, 50), (200, 0), (250, 0)],
)
def test_access_from_distance(d, expected):
    """완만한 감쇠: 100 - d*0.5."""
    assert scoring.access_from_distance(d) == expected


@pytest.mark.parametrize(
    "sky,pty,expected",
    [
        (1, 0, 0),      # 맑음
        (3, 0, 60),     # 구름 많음
        (4, 0, 100),    # 흐림
        (1, 1, 100),    # 강수 형태 있음 -> 강제 100
        (3, 2, 100),
        (None, 0, 0),
    ],
)
def test_cloud_from_kma(sky, pty, expected):
    assert scoring.cloud_from_kma(sky, pty) == expected


def test_moon_from_interference():
    assert scoring.moon_from_interference(0.0) == 100
    assert scoring.moon_from_interference(100.0) == 0
    assert scoring.moon_from_interference(30.0) == 70


def test_compute_score_formula_darkness_mode():
    # 0.35*90 + 0.35*(100-0) + 0.10*100 + 0.20*50 = 31.5+35+10+10 = 86.5 -> 86
    score, bd = scoring.compute_score(darkness=90, cloud=0, moon=100, access=50)
    assert score == 86
    assert bd.darkness == 90 and bd.cloud == 0 and bd.moon == 100 and bd.access == 50


def test_compute_score_nearby_mode_favors_access():
    """근처 모드는 access 가중이 커서, 가까운(access 높은) 곳이 darkness 모드보다 유리하다."""
    # darkness 는 낮지만 access 가 높은 도심 근교 케이스
    dark_mode, _ = scoring.compute_score(40, 0, 100, 90, mode="darkness")
    near_mode, _ = scoring.compute_score(40, 0, 100, 90, mode="nearby")
    assert near_mode > dark_mode


def test_access_gentler_decay():
    """완만한 감쇠: 100km 에서도 50점 (이전엔 0점)."""
    assert scoring.access_from_distance(100) == 50
    assert scoring.access_from_distance(0) == 100
    assert scoring.access_from_distance(200) == 0


def test_compute_score_cloudy_penalizes():
    """구름이 많아지면(cloud 상승) 점수가 낮아진다."""
    clear, _ = scoring.compute_score(90, 0, 100, 50)
    cloudy, _ = scoring.compute_score(90, 100, 100, 50)
    assert cloudy < clear


def test_compute_score_clamped():
    score, _ = scoring.compute_score(200, -5, 999, -10)
    assert 0 <= score <= 100

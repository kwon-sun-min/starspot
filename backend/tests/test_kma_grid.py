"""기상청 격자 변환 단위 테스트.

검증 좌표는 기상청 공식 예제(dfs_xy_conv) 및 널리 공유되는 검증 표에서 가져왔다.
- 서울시청 (37.5714, 126.9658) -> (60, 127)
- 격자 왕복 변환의 일관성 (변환 후 재역변환 시 같은 격자로 수렴)
"""

from __future__ import annotations

import pytest

from app.services.kma_grid import Grid, grid_to_latlon, latlon_to_grid

# (설명, lat, lon, 기대 nx, 기대 ny)
# 서울은 기상청 공식 예제(dfs_xy_conv)의 검증 좌표로 (60, 127)이 확정값이다.
# 나머지 도시는 각 시청 좌표를 검증 알고리즘에 통과시킨 기준 격자다.
OFFICIAL_CASES = [
    ("서울", 37.5714, 126.9658, 60, 127),
    ("부산", 35.1796, 129.0756, 98, 76),
    ("대전", 36.3504, 127.3845, 67, 100),
    ("광주", 35.1595, 126.8526, 58, 74),
    ("대구", 35.8714, 128.6014, 89, 91),
    ("인천", 37.4563, 126.7052, 55, 124),
    ("제주", 33.4996, 126.5312, 53, 38),
    ("강릉", 37.7519, 128.8761, 92, 132),
]


@pytest.mark.parametrize("name,lat,lon,exp_nx,exp_ny", OFFICIAL_CASES)
def test_latlon_to_grid_official(name, lat, lon, exp_nx, exp_ny):
    g = latlon_to_grid(lat, lon)
    assert g == Grid(nx=exp_nx, ny=exp_ny), f"{name}: got {g}, expected ({exp_nx},{exp_ny})"


@pytest.mark.parametrize("name,lat,lon,exp_nx,exp_ny", OFFICIAL_CASES)
def test_roundtrip_grid_latlon(name, lat, lon, exp_nx, exp_ny):
    """격자 중심으로 역변환한 위경도를 다시 격자로 변환하면 동일 격자여야 한다."""
    lat_c, lon_c = grid_to_latlon(exp_nx, exp_ny)
    g = latlon_to_grid(lat_c, lon_c)
    assert g == Grid(nx=exp_nx, ny=exp_ny)


def test_grid_center_close_to_input():
    """입력 좌표와 격자 중심의 오차는 5km 격자 반경(약 0.05도) 이내여야 한다."""
    lat, lon = 37.5714, 126.9658
    g = latlon_to_grid(lat, lon)
    lat_c, lon_c = grid_to_latlon(g.nx, g.ny)
    assert abs(lat_c - lat) < 0.05
    assert abs(lon_c - lon) < 0.05

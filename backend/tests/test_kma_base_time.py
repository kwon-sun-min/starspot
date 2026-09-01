"""기상청 발표시각(base_time) 계산 단위 테스트."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from app.services.kma import compute_base_time

KST = ZoneInfo("Asia/Seoul")


@pytest.mark.parametrize(
    "now_str,exp_date,exp_time",
    [
        # 발표 직후 지연 이내 -> 이전 발표분
        ("2026-09-02 02:05", "20260901", "2300"),   # 02시 발표 미생성 -> 전날 23시
        ("2026-09-02 02:11", "20260902", "0200"),   # 지연 지남 -> 02시 발표
        ("2026-09-02 00:30", "20260901", "2300"),   # 자정 이후 -> 전날 23시
        ("2026-09-02 05:20", "20260902", "0500"),
        ("2026-09-02 13:59", "20260902", "1100"),
        ("2026-09-02 14:15", "20260902", "1400"),
        ("2026-09-02 23:30", "20260902", "2300"),
        ("2026-09-02 20:09", "20260902", "1700"),   # 20:09 는 20시 발표 지연 이내
        ("2026-09-02 20:11", "20260902", "2000"),
    ],
)
def test_compute_base_time(now_str, exp_date, exp_time):
    now = datetime.strptime(now_str, "%Y-%m-%d %H:%M").replace(tzinfo=KST)
    base = compute_base_time(now)
    assert (base.base_date, base.base_time) == (exp_date, exp_time)


def test_compute_base_time_rejects_naive():
    with pytest.raises(ValueError):
        compute_base_time(datetime(2026, 9, 2, 12, 0))

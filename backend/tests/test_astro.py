"""천문 계산 기본 검증 (astronomy-engine 필요)."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

pytest.importorskip("astronomy")

from app.services import astro  # noqa: E402

KST = ZoneInfo("Asia/Seoul")


def test_night_window_is_tz_aware_and_ordered():
    d = datetime(2026, 9, 1, 12, 0, tzinfo=KST)
    win = astro.night_window(37.5714, 126.9658, d)
    assert win is not None
    assert win.sunset.tzinfo is not None
    assert win.sunrise.tzinfo is not None
    # 관측 구간은 일몰 이후 시작, 일출 이전 종료
    assert win.start > win.sunset
    assert win.end < win.sunrise
    assert win.start < win.end
    # 1시간 슬롯이 연속적이어야 한다
    for a, b in zip(win.hours, win.hours[1:], strict=False):
        assert (b - a).total_seconds() == 3600


def test_moon_illumination_range():
    d = datetime(2026, 9, 1, 21, 0, tzinfo=KST)
    _, illum = astro.moon_phase_and_illumination(d)
    assert 0.0 <= illum <= 1.0


def test_moon_interference_range():
    d = datetime(2026, 9, 1, 12, 0, tzinfo=KST)
    idx = astro.moon_interference(37.5714, 126.9658, d)
    assert 0.0 <= idx <= 100.0


def test_naive_datetime_rejected():
    d = datetime(2026, 9, 1, 12, 0)  # naive
    with pytest.raises(ValueError):
        astro.sun_events(37.5714, 126.9658, d)

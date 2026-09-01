"""API 응답 스키마 (Pydantic v2)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class Breakdown(BaseModel):
    darkness: int = Field(ge=0, le=100)
    cloud: int = Field(ge=0, le=100)
    moon: int = Field(ge=0, le=100)
    access: int = Field(ge=0, le=100)


class SpotSummary(BaseModel):
    id: int
    name: str
    category: str
    lat: float
    lon: float
    distance_km: float
    score: int = Field(ge=0, le=100)
    breakdown: Breakdown
    bortle: int | None = None
    best_hour: datetime | None = None


class SpotDetail(BaseModel):
    id: int
    name: str
    category: str
    address: str | None
    lat: float
    lon: float
    elevation_m: int | None
    radiance: float | None
    darkness_score: int | None
    bortle: int | None


class HourlyScore(BaseModel):
    hour: datetime
    score: int
    cloud: int
    moon: int


class ForecastResponse(BaseModel):
    spot_id: int
    date: str
    hourly: list[HourlyScore]
    best_hour: datetime | None
    best_score: int
    stale: bool = False


class AstroResponse(BaseModel):
    sunset: datetime | None
    sunrise: datetime | None
    moonrise: datetime | None
    moonset: datetime | None
    moon_phase_deg: float
    moon_illumination: float

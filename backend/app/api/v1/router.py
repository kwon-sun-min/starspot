"""v1 라우터 집합."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import astro, health, metrics, spots

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(spots.router)
api_router.include_router(astro.router)
api_router.include_router(metrics.router)

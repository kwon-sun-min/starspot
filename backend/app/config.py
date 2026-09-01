"""애플리케이션 설정. 모든 값은 환경변수에서 로드한다 (시크릿 하드코딩 금지)."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # 필수 인프라 연결
    database_url: str = "postgresql+psycopg://starspot:starspot@localhost:5432/starspot"
    redis_url: str = "redis://localhost:6379/0"

    # 외부 API
    kma_service_key: str = ""

    # 애플리케이션
    tz: str = "Asia/Seoul"
    log_level: str = "INFO"

    # 캐시 TTL (초) — 기상청 발표 주기(3시간)와 맞춤
    kma_cache_ttl: int = 3 * 60 * 60


@lru_cache
def get_settings() -> Settings:
    return Settings()

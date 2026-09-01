"""backend/data/spots.csv 를 PostGIS에 적재하는 시드 스크립트.

스키마는 Alembic 마이그레이션이 소유한다. 이 스크립트는 데이터 적재만 담당한다.
사전 조건: `alembic upgrade head` 로 spots 테이블이 생성되어 있어야 한다.

- kma_nx/ny 를 적재 시점에 미리 계산해 저장한다 (기상청 호출 절감의 핵심).
- geom 은 GEOGRAPHY(POINT, 4326) 로 저장한다.
- radiance/darkness_score/bortle 은 아직 없으므로 NULL 로 둔다
  (extract_radiance.py 실행 결과를 UPDATE 하기 전 상태).

실행:
    DATABASE_URL=postgresql+psycopg://starspot:starspot@localhost:5432/starspot \
        python -m scripts.seed_spots
"""

from __future__ import annotations

import csv
import os

# app 패키지의 격자 변환 함수 재사용
import sys
from pathlib import Path

from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.kma_grid import latlon_to_grid  # noqa: E402

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "spots.csv"

UPSERT = text(
    """
    INSERT INTO spots (name, category, address, geom, elevation_m, kma_nx, kma_ny)
    VALUES (
        :name, :category, :address,
        ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
        :elevation_m, :kma_nx, :kma_ny
    )
    """
)


def _database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise SystemExit("DATABASE_URL 환경변수가 필요합니다.")
    return url


def seed() -> int:
    engine = create_engine(_database_url(), future=True)
    with engine.begin() as conn:
        # 스키마는 Alembic 이 생성한다. 재실행 시 중복 방지를 위해 테이블만 비운다.
        conn.execute(text("TRUNCATE spots RESTART IDENTITY"))

        inserted = 0
        with DATA_PATH.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                lat = round(float(row["lat"]), 6)
                lon = round(float(row["lon"]), 6)
                grid = latlon_to_grid(lat, lon)
                conn.execute(
                    UPSERT,
                    {
                        "name": row["name"],
                        "category": row["category"],
                        "address": row.get("address") or None,
                        "lat": lat,
                        "lon": lon,
                        "elevation_m": int(row["elevation_m"]) if row.get("elevation_m") else None,
                        "kma_nx": grid.nx,
                        "kma_ny": grid.ny,
                    },
                )
                inserted += 1
    print(f"seeded {inserted} spots")
    return inserted


if __name__ == "__main__":
    seed()

"""crop된 VIIRS 래스터에서 각 후보지의 radiance를 샘플링해 DB를 갱신한다.

각 후보지 좌표(lon, lat)에서 radiance(nW/cm²/sr)를 읽어:
  - radiance 컬럼에 저장
  - darkness_score = 런타임 scoring.darkness_from_radiance() 와 동일 공식 (일관성)
  - bortle = radiance 임계값 기반 근사 등급(1~9)

DB 갱신만 하므로 spots 테이블은 이미 시드되어 있어야 한다.

사용:
    DATABASE_URL=postgresql+psycopg://starspot:starspot@localhost:5432/starspot \
        python -m scripts.extract_radiance --raster data/viirs_korea.tif
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.scoring import darkness_from_radiance  # noqa: E402

# Bortle 근사: VIIRS radiance(nW/cm²/sr) 임계값 -> 등급.
# 값이 낮을수록(어두울수록) 등급이 낮다(=좋다). 대략적 매핑이다.
_BORTLE_THRESHOLDS = [
    (0.25, 1),   # 매우 어두움
    (0.50, 2),
    (1.00, 3),
    (3.00, 4),
    (6.00, 5),
    (12.0, 6),
    (25.0, 7),
    (50.0, 8),
]


def bortle_from_radiance(radiance: float) -> int:
    for threshold, grade in _BORTLE_THRESHOLDS:
        if radiance <= threshold:
            return grade
    return 9  # 도심 최악


def _database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise SystemExit("DATABASE_URL 환경변수가 필요합니다.")
    return url


def extract(raster_path: str) -> int:
    import rasterio

    engine = create_engine(_database_url(), future=True)

    with engine.connect() as conn:
        spots = conn.execute(
            text(
                "SELECT id, ST_Y(geom::geometry) AS lat, ST_X(geom::geometry) AS lon FROM spots"
            )
        ).mappings().all()

    updated = 0
    with rasterio.open(raster_path) as src:
        band = src.read(1)
        nodata = src.nodata
        height, width = band.shape

        with engine.begin() as conn:
            for s in spots:
                lon, lat = s["lon"], s["lat"]
                # 좌표 -> 픽셀 인덱스
                row, col = src.index(lon, lat)
                if not (0 <= row < height and 0 <= col < width):
                    continue  # bbox 밖
                value = float(band[row, col])
                if nodata is not None and value == nodata:
                    continue
                radiance = max(0.0, value)
                conn.execute(
                    text(
                        """
                        UPDATE spots
                        SET radiance = :radiance,
                            darkness_score = :darkness,
                            bortle = :bortle
                        WHERE id = :id
                        """
                    ),
                    {
                        "radiance": radiance,
                        "darkness": darkness_from_radiance(radiance),
                        "bortle": bortle_from_radiance(radiance),
                        "id": s["id"],
                    },
                )
                updated += 1

    print(f"updated radiance for {updated}/{len(spots)} spots")
    return updated


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract VIIRS radiance per spot")
    parser.add_argument("--raster", default="data/viirs_korea.tif", help="crop된 래스터 경로")
    args = parser.parse_args()
    extract(args.raster)


if __name__ == "__main__":
    main()

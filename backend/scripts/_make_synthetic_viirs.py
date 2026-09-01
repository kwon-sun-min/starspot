"""[검증 전용] 합성 VIIRS 래스터 생성.

실제 전지구 VNL 대신, 한반도 주변을 덮는 작은 GeoTIFF를 만든다.
- 대부분 어두운 시골(radiance ~0.3)
- 서울/수도권 근처에 밝은 도심 패치(radiance ~60)
crop_viirs / extract_radiance 파이프라인 검증에만 사용한다.
"""

from __future__ import annotations

import numpy as np
import rasterio
from rasterio.transform import from_origin

# 살짝 여유있게 잡은 영역 (crop bbox 124-132, 33-39 를 포함)
MIN_LON, MAX_LON = 120.0, 135.0
MIN_LAT, MAX_LAT = 30.0, 42.0
RES = 0.01  # 도 단위 픽셀 크기


def main(out: str = "data/viirs_global.tif") -> None:
    width = int(round((MAX_LON - MIN_LON) / RES))
    height = int(round((MAX_LAT - MIN_LAT) / RES))
    transform = from_origin(MIN_LON, MAX_LAT, RES, RES)

    # 기본: 어두운 시골
    data = np.full((height, width), 0.3, dtype="float32")

    def set_patch(lon: float, lat: float, radius_deg: float, value: float) -> None:
        cx = int((lon - MIN_LON) / RES)
        cy = int((MAX_LAT - lat) / RES)
        r = int(radius_deg / RES)
        y0, y1 = max(0, cy - r), min(height, cy + r)
        x0, x1 = max(0, cx - r), min(width, cx + r)
        data[y0:y1, x0:x1] = value

    # 서울/수도권 (밝음)
    set_patch(126.978, 37.5665, 0.5, 60.0)
    # 부산 (밝음)
    set_patch(129.075, 35.18, 0.3, 45.0)
    # 안성 근처 (약간 밝음) - 안성맞춤천문과학관 주변
    set_patch(127.246, 37.019, 0.15, 8.0)

    profile = {
        "driver": "GTiff",
        "height": height,
        "width": width,
        "count": 1,
        "dtype": "float32",
        "crs": "EPSG:4326",
        "transform": transform,
        "nodata": -999.0,
    }
    with rasterio.open(out, "w", **profile) as dst:
        dst.write(data, 1)
    print(f"synthetic raster: {out} ({width}x{height})")


if __name__ == "__main__":
    main()

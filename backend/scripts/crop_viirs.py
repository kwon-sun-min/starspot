"""전지구 VIIRS VNL 연간 합성 GeoTIFF를 한반도 영역으로 crop.

EOG(Earth Observation Group)의 VNL(VIIRS Nighttime Lights) 연간 합성본은
전지구 15 arc-second 해상도로 수 GB에 달한다. 전체를 메모리에 올리면 안 되므로
rasterio 의 윈도우 읽기(Window)로 한반도 bbox 영역만 잘라 저장한다.

한반도 bbox: 124.0E ~ 132.0E, 33.0N ~ 39.0N

사용:
    python -m scripts.crop_viirs \
        --src data/viirs_global.tif \
        --dst data/viirs_korea.tif

의존성: rasterio (pyproject 의 [batch] extra). 런타임 서비스에는 포함되지 않는다.
"""

from __future__ import annotations

import argparse
from pathlib import Path

# 한반도 bounding box (경도/위도)
KOREA_BBOX = (124.0, 33.0, 132.0, 39.0)  # (min_lon, min_lat, max_lon, max_lat)


def crop(
    src_path: str,
    dst_path: str,
    bbox: tuple[float, float, float, float] = KOREA_BBOX,
) -> None:
    import rasterio
    from rasterio.windows import from_bounds

    min_lon, min_lat, max_lon, max_lat = bbox
    with rasterio.open(src_path) as src:
        # bbox 를 픽셀 윈도우로 변환 (전체 로드 없이 해당 영역만 읽는다)
        window = from_bounds(min_lon, min_lat, max_lon, max_lat, transform=src.transform)
        window = window.round_offsets().round_lengths()

        data = src.read(1, window=window)
        win_transform = src.window_transform(window)

        profile = src.profile.copy()
        profile.update(
            {
                "height": data.shape[0],
                "width": data.shape[1],
                "transform": win_transform,
                "compress": "deflate",
                # tiled TIFF 는 블록 크기가 16 배수여야 하므로, crop 크기가 임의일 수 있는
                # 이 경우 striped(비타일) 로 저장한다.
                "tiled": False,
            }
        )

        Path(dst_path).parent.mkdir(parents=True, exist_ok=True)
        with rasterio.open(dst_path, "w", **profile) as dst:
            dst.write(data, 1)

    print(
        f"cropped {src_path} -> {dst_path} "
        f"({data.shape[1]}x{data.shape[0]} px, bbox={bbox})"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Crop global VIIRS VNL to Korea bbox")
    parser.add_argument("--src", required=True, help="전지구 VNL GeoTIFF 경로")
    parser.add_argument("--dst", default="data/viirs_korea.tif", help="출력 경로")
    args = parser.parse_args()
    crop(args.src, args.dst)


if __name__ == "__main__":
    main()

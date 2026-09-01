#!/usr/bin/env bash
# VIIRS VNL 연간 합성 GeoTIFF 다운로드 헬퍼.
#
# 원본은 EOG(Earth Observation Group, Colorado School of Mines)에서 제공한다.
# 파일이 수 GB 이므로 리포지토리에 커밋하지 않는다 (.gitignore 로 제외).
# 다운로드 후 crop_viirs.py 로 한반도 영역만 잘라 사용한다.
#
# 사전 준비:
#   1) https://eogdata.mines.edu/products/vnl/ 에서 최신 연간 합성본 URL 확인
#      (예: VNL v2 median-masked, average_masked 등)
#   2) EOG 계정 토큰이 필요할 수 있음 (문서 참조).
#
# 사용:
#   VIIRS_URL="https://eogdata.mines.edu/.../VNL_....tif.gz" ./scripts/download_viirs.sh
set -euo pipefail

DEST_DIR="${DEST_DIR:-data}"
OUT="${DEST_DIR}/viirs_global.tif"

if [[ -z "${VIIRS_URL:-}" ]]; then
  echo "VIIRS_URL 환경변수에 다운로드 URL을 지정하세요." >&2
  echo "예: VIIRS_URL='https://eogdata.mines.edu/.../VNL_....tif.gz' $0" >&2
  exit 1
fi

mkdir -p "$DEST_DIR"

echo "downloading VIIRS VNL -> ${OUT} ..."
if [[ "$VIIRS_URL" == *.gz ]]; then
  curl -fL "$VIIRS_URL" -o "${OUT}.gz"
  echo "decompressing ..."
  gunzip -f "${OUT}.gz"
else
  curl -fL "$VIIRS_URL" -o "$OUT"
fi

echo "done: ${OUT}"
echo "다음 단계: python -m scripts.crop_viirs --src ${OUT} --dst ${DEST_DIR}/viirs_korea.tif"

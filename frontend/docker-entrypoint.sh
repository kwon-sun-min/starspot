#!/bin/sh
set -e

# 런타임에 KAKAO_MAP_KEY 를 env.js 로 주입 (이미지 재빌드 없이 키 교체 가능).
cat > /usr/share/nginx/html/env.js <<EOF
window.__ENV__ = {
  KAKAO_MAP_KEY: "${KAKAO_MAP_KEY:-}"
};
EOF

exec nginx -g "daemon off;"

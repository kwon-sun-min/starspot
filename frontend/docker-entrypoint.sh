#!/bin/sh
set -e

# 런타임에 KAKAO_MAP_KEY 를 env.js 로 주입 (이미지 재빌드 없이 키 교체 가능).
cat > /usr/share/nginx/html/env.js <<EOF
window.__ENV__ = {
  KAKAO_MAP_KEY: "${KAKAO_MAP_KEY:-}"
};
EOF

# nginx 설정 렌더링 (배포 환경별 프록시 업스트림/포트 주입).
#  - NGINX_PORT: 리스닝 포트. Railway 는 $PORT 를 주입하므로 그 값을 쓴다(없으면 80).
#  - API_UPSTREAM: /api 프록시 대상. 로컬 compose 는 http://api:8000.
export NGINX_PORT="${PORT:-80}"
export API_UPSTREAM="${API_UPSTREAM:-http://api:8000}"
# 컨테이너의 DNS 리졸버(런타임 업스트림 해석용). resolv.conf 첫 nameserver, 없으면 127.0.0.11(docker).
export DNS_RESOLVER="$(awk '/^nameserver/ {print $2; exit}' /etc/resolv.conf 2>/dev/null || echo 127.0.0.11)"

envsubst '${NGINX_PORT} ${API_UPSTREAM} ${DNS_RESOLVER}' \
  < /etc/nginx/templates/default.conf.template \
  > /etc/nginx/conf.d/default.conf

exec nginx -g "daemon off;"

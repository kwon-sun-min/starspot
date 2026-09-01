# syntax=docker/dockerfile:1
# 빌드 컨텍스트는 리포지토리 루트(.) 이다 (docker-compose 의 nginx.build.context: .).
# 이렇게 해야 infra/nginx/default.conf 를 이미지에 넣을 수 있다.

# ---- build stage ----
FROM node:22-alpine AS build
WORKDIR /app
COPY frontend/package.json ./
# lockfile 이 없으므로 install (CI 에서는 npm ci 권장)
RUN npm install
COPY frontend/ ./
RUN npm run build

# ---- serve stage (nginx) ----
FROM nginx:1.27-alpine AS runtime
COPY --from=build /app/dist /usr/share/nginx/html
COPY infra/nginx/default.conf /etc/nginx/conf.d/default.conf
COPY frontend/docker-entrypoint.sh /docker-entrypoint-custom.sh
RUN chmod +x /docker-entrypoint-custom.sh
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -q -O /dev/null http://127.0.0.1/ || exit 1
ENTRYPOINT ["/docker-entrypoint-custom.sh"]

# syntax=docker/dockerfile:1

# ---- builder ----
FROM python:3.12-slim AS builder
WORKDIR /app
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
COPY pyproject.toml ./
# 런타임 의존성만 설치 (batch 는 제외 = rasterio 불필요)
RUN pip install --prefix=/install \
    "fastapi>=0.115" "uvicorn[standard]>=0.32" "pydantic>=2.9" "pydantic-settings>=2.6" \
    "sqlalchemy>=2.0" "geoalchemy2>=0.15" "psycopg[binary]>=3.2" "alembic>=1.13" \
    "httpx>=0.27" "redis>=5.1" "astronomy-engine>=2.1.19" "apscheduler>=3.10" "tenacity>=9.0" \
    "prometheus-client>=0.21"

# ---- runtime ----
FROM python:3.12-slim AS runtime
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 TZ=Asia/Seoul
WORKDIR /app
COPY --from=builder /install /usr/local
COPY . .

# non-root 유저
RUN useradd -m -u 10001 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request,sys; urllib.request.urlopen('http://localhost:8000/api/v1/health'); " || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

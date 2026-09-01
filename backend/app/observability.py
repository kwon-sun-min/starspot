"""Prometheus 메트릭 정의 + 요청 추적 컨텍스트.

노출 메트릭 (Grafana 대시보드용):
- starspot_http_requests_total{method,path,status}      요청 카운터
- starspot_http_request_duration_seconds{method,path}   지연 히스토그램
- starspot_cache_events_total{result}                   캐시 hit/miss/stale
- starspot_kma_requests_total{outcome}                  외부 API 성공/실패
"""

from __future__ import annotations

import contextvars

from prometheus_client import Counter, Histogram

# 요청 추적 ID (미들웨어가 세팅, 로깅 필터가 읽음)
request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")

HTTP_REQUESTS = Counter(
    "starspot_http_requests_total",
    "HTTP 요청 수",
    ["method", "path", "status"],
)

HTTP_LATENCY = Histogram(
    "starspot_http_request_duration_seconds",
    "HTTP 요청 지연(초)",
    ["method", "path"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

CACHE_EVENTS = Counter(
    "starspot_cache_events_total",
    "기상청 캐시 이벤트",
    ["result"],  # hit | miss | stale
)

KMA_REQUESTS = Counter(
    "starspot_kma_requests_total",
    "기상청 외부 API 호출 결과",
    ["outcome"],  # success | failure
)

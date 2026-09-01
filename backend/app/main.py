"""FastAPI 애플리케이션 엔트리포인트."""

from __future__ import annotations

import logging
import time
import uuid

from fastapi import FastAPI, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.api.v1.router import api_router
from app.config import get_settings
from app.logging_config import configure_logging
from app.observability import HTTP_LATENCY, HTTP_REQUESTS, request_id_ctx

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger("starspot")


def _route_template(request: Request) -> str:
    """메트릭 카디널리티 폭발을 막기 위해 실제 경로 대신 라우트 템플릿을 쓴다.

    예: /api/v1/spots/42 -> /api/v1/spots/{spot_id}
    """
    route = request.scope.get("route")
    return getattr(route, "path", request.url.path)


def create_app() -> FastAPI:
    app = FastAPI(title="StarSpot API", version="0.1.0")

    @app.middleware("http")
    async def observe(request: Request, call_next):
        request_id = request.headers.get("x-request-id", uuid.uuid4().hex[:12])
        token = request_id_ctx.set(request_id)
        start = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            request_id_ctx.reset(token)
        duration = time.perf_counter() - start

        path_tmpl = _route_template(request)
        HTTP_REQUESTS.labels(
            method=request.method, path=path_tmpl, status=str(response.status_code)
        ).inc()
        HTTP_LATENCY.labels(method=request.method, path=path_tmpl).observe(duration)

        logger.info(
            "request",
            extra={
                "path": request.url.path,
                "method": request.method,
                "status": response.status_code,
                "duration_ms": round(duration * 1000, 2),
                "request_id": request_id,
            },
        )
        response.headers["x-request-id"] = request_id
        return response

    @app.get("/metrics", include_in_schema=False)
    def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    app.include_router(api_router)
    return app


app = create_app()

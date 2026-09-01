"""구조적(JSON) 로깅 설정. 요청 추적을 위한 최소 구성."""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "request_id": _current_request_id(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        # 미들웨어가 명시적으로 넘긴 필드는 덮어쓴다
        for key in ("path", "method", "status", "duration_ms", "request_id"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        return json.dumps(payload, ensure_ascii=False)


def _current_request_id() -> str:
    """관측성 모듈의 contextvar 에서 현재 요청 추적 ID 를 읽는다."""
    try:
        from app.observability import request_id_ctx

        return request_id_ctx.get()
    except Exception:  # noqa: BLE001
        return "-"


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())

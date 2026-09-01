"""예보 프리페치 배치 워커.

발표 시각(02/05/08/11/14/17/20/23시) 직후에 DB의 모든 고유 격자에 대해 기상청 예보를
미리 조회해 캐시를 채운다. 이로써 사용자 요청은 항상 캐시 히트가 된다.

- 발표 지연(약 10분)을 고려해 각 발표시각 +15분에 실행.
- 서로 다른 후보지가 같은 격자를 공유하므로, DISTINCT (kma_nx, kma_ny) 만 조회한다.
- 실행은 컨테이너의 worker 서비스(python -m app.workers.refresh)로 상시 구동.
"""

from __future__ import annotations

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import text

from app.config import get_settings
from app.db import SessionLocal
from app.logging_config import configure_logging
from app.services.kma import compute_base_time, fetch_forecast

logger = logging.getLogger("starspot.worker")

# 발표시각 + 15분에 프리페치
_PREFETCH_MINUTE = 15
_BASE_HOURS = [2, 5, 8, 11, 14, 17, 20, 23]


def _distinct_grids() -> list[tuple[int, int]]:
    with SessionLocal() as db:
        rows = db.execute(
            text("SELECT DISTINCT kma_nx, kma_ny FROM spots")
        ).all()
    return [(int(r[0]), int(r[1])) for r in rows]


async def prefetch_all() -> dict[str, int]:
    """모든 고유 격자의 예보를 캐시에 채운다. 결과 요약을 반환."""
    base = compute_base_time()
    grids = _distinct_grids()
    ok = 0
    failed = 0
    for nx, ny in grids:
        try:
            await fetch_forecast(nx, ny, base)
            ok += 1
        except Exception as e:  # noqa: BLE001
            failed += 1
            logger.warning(
                "prefetch failed for grid %s,%s: %s", nx, ny, str(e)
            )
    summary = {"grids": len(grids), "ok": ok, "failed": failed}
    logger.info(
        "prefetch done grids=%s ok=%s failed=%s", summary["grids"], summary["ok"], summary["failed"]
    )
    return summary


def _schedule(scheduler: AsyncIOScheduler) -> None:
    hours = ",".join(str(h) for h in _BASE_HOURS)
    scheduler.add_job(
        prefetch_all,
        CronTrigger(hour=hours, minute=_PREFETCH_MINUTE, timezone=get_settings().tz),
        id="kma_prefetch",
        max_instances=1,
        coalesce=True,
    )


async def main() -> None:
    configure_logging(get_settings().log_level)
    logger.info("worker starting")
    # 기동 즉시 1회 프리페치(콜드 스타트 대비)
    await prefetch_all()

    scheduler = AsyncIOScheduler()
    _schedule(scheduler)
    scheduler.start()
    logger.info("scheduler started")

    # 이벤트 루프 유지
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, asyncio.CancelledError):
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())

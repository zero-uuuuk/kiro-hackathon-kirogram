"""스케줄러 라우터 — 매일 06:00 KST 공고 자동 수집."""

import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import APIRouter

from scrapers import samsung
from scrapers import cj
from scrapers.ingestor import ingest_to_db

router = APIRouter(prefix="/scheduler", tags=["scheduler"])
scheduler = AsyncIOScheduler(timezone="Asia/Seoul")


async def _collect_all():
    """삼성 + CJ 공고 수집 후 DB 저장."""
    await asyncio.to_thread(samsung.main)
    await asyncio.to_thread(cj.main)
    await ingest_to_db()


def start_scheduler():
    scheduler.add_job(
        _collect_all,
        CronTrigger(hour=6, minute=0, timezone="Asia/Seoul"),
        id="daily_job_collect",
        replace_existing=True,
    )
    scheduler.start()


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)


@router.post("/run-now", status_code=202)
async def run_now():
    """수동으로 공고 수집을 즉시 트리거한다."""
    asyncio.create_task(_collect_all())
    return {"message": "공고 수집 시작됨"}

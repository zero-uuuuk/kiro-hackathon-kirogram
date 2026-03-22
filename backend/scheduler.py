"""Daily scheduler — runs crawler then recommender at a configured hour (KST)."""

import asyncio
import logging
import os
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

SCHEDULE_HOUR = int(os.getenv("CRAWL_SCHEDULE_HOUR", "9"))
TIMEZONE = "Asia/Seoul"


async def _cleanup_expired_posts() -> None:
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine
    from crawler.config import DATABASE_URL

    url = DATABASE_URL
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    engine = create_async_engine(url)
    try:
        async with engine.begin() as conn:
            result = await conn.execute(
                text("DELETE FROM posts WHERE deadline IS NOT NULL AND deadline < NOW()")
            )
            logger.info("Expired post cleanup: deleted %d posts", result.rowcount)
    finally:
        await engine.dispose()


async def daily_job() -> None:
    start = datetime.now()
    logger.info("Daily job started at %s", start.isoformat())

    # 1) Crawl
    try:
        from crawler.orchestrator import run as run_crawler
        logger.info("Starting crawler...")
        await run_crawler()
        logger.info("Crawler finished.")
    except Exception:
        logger.exception("Crawler failed")

    # 2) Clean up expired posts (cascade-deletes ai_recommendations via FK)
    try:
        await _cleanup_expired_posts()
    except Exception:
        logger.exception("Expired post cleanup failed")

    # 3) Recommend (since = last 25h to catch stragglers)
    try:
        from recommender.agent import RecommenderAgent
        since = datetime.utcnow() - timedelta(hours=25)
        logger.info("Starting recommender (since=%s)...", since.isoformat())
        agent = RecommenderAgent()
        await agent.run(since=since)
        logger.info("Recommender finished.")
    except Exception:
        logger.exception("Recommender failed")

    end = datetime.now()
    logger.info("Daily job ended at %s (took %s)", end.isoformat(), end - start)


def main() -> None:
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    scheduler.add_job(daily_job, "cron", hour=SCHEDULE_HOUR, minute=0)
    scheduler.start()
    logger.info(
        "Scheduler started — daily job at %02d:00 %s", SCHEDULE_HOUR, TIMEZONE
    )
    try:
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")


if __name__ == "__main__":
    main()

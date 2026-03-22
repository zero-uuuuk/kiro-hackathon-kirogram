"""FastAPI 앱 진입점."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import get_pool, close_pool
from routers import users, cv, jobs, recommendations
from routers.scheduler import router as scheduler_router, start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    pool = await get_pool()
    await pool.execute(
        "ALTER TABLE ai_recommendations ADD COLUMN IF NOT EXISTS weaknesses JSONB DEFAULT '[]'"
    )
    await pool.execute(
        "ALTER TABLE ai_recommendations ADD COLUMN IF NOT EXISTS strengths JSONB DEFAULT '[]'"
    )
    await pool.execute("ALTER TABLE job_postings ADD COLUMN IF NOT EXISTS source TEXT")
    await pool.execute("ALTER TABLE job_postings ADD COLUMN IF NOT EXISTS url TEXT")
    start_scheduler()
    yield
    stop_scheduler()
    await close_pool()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(cv.router)
app.include_router(jobs.router)
app.include_router(recommendations.router)
app.include_router(scheduler_router)

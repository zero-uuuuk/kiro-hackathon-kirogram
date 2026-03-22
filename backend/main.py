"""FastAPI 앱 진입점."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import get_pool, close_pool
from routers import users, cv, jobs, recommendations


@asynccontextmanager
async def lifespan(app: FastAPI):
    await get_pool()
    yield
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

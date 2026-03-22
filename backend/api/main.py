"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine

load_dotenv()

import os

from api.auth import router as auth_router
from api.routes import router
from api.calendar import router as calendar_router
from api.user_routes import router as user_router
from api.source_routes import router as source_router

DATABASE_URL = os.getenv("DATABASE_URL", "")


def _async_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.engine = create_async_engine(_async_url(DATABASE_URL))
    yield
    await app.state.engine.dispose()


app = FastAPI(lifespan=lifespan)
app.include_router(router)
app.include_router(auth_router)
app.include_router(calendar_router)
app.include_router(user_router)
app.include_router(source_router)

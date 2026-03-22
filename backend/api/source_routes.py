"""Custom sources endpoints — user-registered URLs with natural language description."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import text

router = APIRouter()


class SourceCreate(BaseModel):
    url: str
    description: str | None = None


class SourceResponse(BaseModel):
    id: int
    user_id: int
    url: str
    description: str | None
    is_active: bool


@router.get("/users/{user_id}/sources", response_model=list[SourceResponse])
async def list_sources(request: Request, user_id: int):
    async with request.app.state.engine.connect() as conn:
        rows = (await conn.execute(
            text("SELECT id, user_id, url, description, is_active FROM custom_sources WHERE user_id = :uid ORDER BY id"),
            {"uid": user_id},
        )).mappings().all()
    return [dict(r) for r in rows]


@router.post("/users/{user_id}/sources", response_model=SourceResponse, status_code=201)
async def add_source(request: Request, user_id: int, body: SourceCreate):
    async with request.app.state.engine.begin() as conn:
        row = (await conn.execute(
            text("""
                INSERT INTO custom_sources (user_id, url, description)
                VALUES (:uid, :url, :desc)
                ON CONFLICT (user_id, url) DO UPDATE SET description = EXCLUDED.description
                RETURNING id, user_id, url, description, is_active
            """),
            {"uid": user_id, "url": body.url, "desc": body.description},
        )).mappings().one()
    return dict(row)


@router.delete("/users/{user_id}/sources/{source_id}", status_code=204)
async def delete_source(request: Request, user_id: int, source_id: int):
    async with request.app.state.engine.begin() as conn:
        result = await conn.execute(
            text("DELETE FROM custom_sources WHERE id = :sid AND user_id = :uid"),
            {"sid": source_id, "uid": user_id},
        )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Source not found")

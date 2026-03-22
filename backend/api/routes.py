"""Notification endpoints."""

from typing import List

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel
from sqlalchemy import text

router = APIRouter()


class ReadRequest(BaseModel):
    user_id: int
    post_ids: List[int]


@router.get("/notifications")
async def get_notifications(request: Request, user_id: int = Query(...)):
    engine = request.app.state.engine
    stmt = text("""
        SELECT r.post_id, p.title, p.company, p.deadline, p.category,
               r.reason, r.todos, r.relevance_score
        FROM ai_recommendations r
        JOIN posts p ON p.id = r.post_id
        WHERE r.user_id = :user_id AND r.is_read = FALSE
          AND (p.deadline IS NULL OR p.deadline > NOW())
        ORDER BY r.relevance_score DESC NULLS LAST
    """)
    async with engine.connect() as conn:
        rows = (await conn.execute(stmt, {"user_id": user_id})).mappings().all()
    return [
        {
            "post_id": r["post_id"],
            "title": r["title"],
            "company": r["company"],
            "deadline": r["deadline"].isoformat() if r["deadline"] else None,
            "category": r["category"],
            "reason": r["reason"],
            "todos": r["todos"],
            "relevance_score": r["relevance_score"],
        }
        for r in rows
    ]


@router.post("/notifications/read")
async def mark_read(request: Request, body: ReadRequest):
    engine = request.app.state.engine
    stmt = text("""
        UPDATE ai_recommendations
        SET is_read = TRUE
        WHERE user_id = :user_id AND post_id = ANY(:post_ids)
    """)
    async with engine.begin() as conn:
        await conn.execute(stmt, {"user_id": body.user_id, "post_ids": body.post_ids})
    return {"status": "ok"}

"""Google Calendar event registration and listing endpoints."""

from fastapi import APIRouter, HTTPException, Query, Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from pydantic import BaseModel
from sqlalchemy import text

router = APIRouter()


class RegisterRequest(BaseModel):
    user_id: int
    post_id: int


@router.post("/calendar/register")
async def register_event(request: Request, body: RegisterRequest):
    engine = request.app.state.engine

    async with engine.connect() as conn:
        user = (await conn.execute(
            text("SELECT google_calendar_token FROM users WHERE id = :uid"),
            {"uid": body.user_id},
        )).mappings().first()
        if not user or not user["google_calendar_token"]:
            raise HTTPException(400, "Google Calendar not connected")

        post = (await conn.execute(
            text("SELECT title, deadline FROM posts WHERE id = :pid"),
            {"pid": body.post_id},
        )).mappings().first()
        if not post:
            raise HTTPException(404, "Post not found")
        if not post["deadline"]:
            raise HTTPException(400, "Post has no deadline")

    token_dict = user["google_calendar_token"]
    creds = Credentials.from_authorized_user_info(token_dict)
    service = build("calendar", "v3", credentials=creds)

    event_date = post["deadline"].strftime("%Y-%m-%d")
    event = service.events().insert(
        calendarId="primary",
        body={
            "summary": post["title"],
            "start": {"date": event_date},
            "end": {"date": event_date},
        },
    ).execute()

    async with engine.begin() as conn:
        await conn.execute(
            text("""
                INSERT INTO calendar_events (user_id, post_id, google_event_id, event_date, is_registered, registered_at)
                VALUES (:uid, :pid, :geid, :edate, TRUE, NOW())
                ON CONFLICT (user_id, post_id) DO UPDATE
                SET google_event_id = :geid, is_registered = TRUE, registered_at = NOW()
            """),
            {"uid": body.user_id, "pid": body.post_id, "geid": event["id"], "edate": event_date},
        )
    return {"status": "ok", "google_event_id": event["id"]}


@router.get("/calendar")
async def get_calendar(request: Request, user_id: int = Query(...)):
    engine = request.app.state.engine
    async with engine.connect() as conn:
        rows = (await conn.execute(
            text("""
                SELECT ce.id, ce.post_id, p.title, p.company, p.deadline, p.category,
                       ce.google_event_id, ce.event_date, ce.start_date, ce.end_date,
                       ce.is_range, ce.is_registered, ce.registered_at
                FROM calendar_events ce
                JOIN posts p ON p.id = ce.post_id
                WHERE ce.user_id = :uid
                ORDER BY ce.event_date
            """),
            {"uid": user_id},
        )).mappings().all()
    return [
        {
            "id": r["id"],
            "post_id": r["post_id"],
            "title": r["title"],
            "company": r["company"],
            "deadline": r["deadline"].isoformat() if r["deadline"] else None,
            "category": r["category"],
            "google_event_id": r["google_event_id"],
            "event_date": r["event_date"].isoformat() if r["event_date"] else None,
            "start_date": r["start_date"].isoformat() if r["start_date"] else None,
            "end_date": r["end_date"].isoformat() if r["end_date"] else None,
            "is_range": r["is_range"],
            "is_registered": r["is_registered"],
            "registered_at": r["registered_at"].isoformat() if r["registered_at"] else None,
        }
        for r in rows
    ]

"""Google OAuth login, JWT issuance, and profile completion."""

import json
import os
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from jose import jwt
from pydantic import BaseModel
from sqlalchemy import text

router = APIRouter()

JWT_SECRET = os.getenv("JWT_SECRET", "changeme")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = 30

SCOPES = [
    "openid",
    "email",
    "profile",
    "https://www.googleapis.com/auth/calendar.events",
]


def _build_flow() -> Flow:
    client_config = {
        "web": {
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }
    flow = Flow.from_client_config(client_config, scopes=SCOPES)
    flow.redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
    return flow


def _create_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRE_DAYS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _verify_token(authorization: str) -> int:
    if not authorization:
        raise HTTPException(401, "Missing authorization header")
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Invalid authorization header")
    token = authorization[7:]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return int(payload["sub"])
    except Exception:
        raise HTTPException(401, "Invalid or expired token")


@router.get("/auth/login")
async def login():
    flow = _build_flow()
    url, _ = flow.authorization_url(prompt="consent", access_type="offline", state="login")
    return RedirectResponse(url)


@router.get("/auth/callback")
async def callback(request: Request, code: str = Query(...), state: str = Query(...)):
    flow = _build_flow()
    flow.fetch_token(code=code)
    credentials = flow.credentials
    token_dict = json.loads(credentials.to_json())

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {credentials.token}"},
        )
        resp.raise_for_status()
        userinfo = resp.json()

    email = userinfo["email"]
    name = userinfo.get("name", "")

    engine = request.app.state.engine
    async with engine.begin() as conn:
        row = (await conn.execute(
            text("""
                INSERT INTO users (email, name, school, major, enrollment_status, grade, info_focus, google_calendar_token)
                VALUES (:email, :name, '', '', 'enrolled', '1', '{}', :token)
                ON CONFLICT (email) DO UPDATE
                SET name = EXCLUDED.name, google_calendar_token = EXCLUDED.google_calendar_token
                RETURNING id, (xmax = 0) AS is_new
            """),
            {"email": email, "name": name, "token": json.dumps(token_dict)},
        )).mappings().first()

    user_id = row["id"]
    is_new = row["is_new"]
    access_token = _create_token(user_id)
    return {"access_token": access_token, "user_id": user_id, "is_new": is_new}


class ProfileRequest(BaseModel):
    school: str
    major: str
    enrollment_status: str = "enrolled"
    grade: str
    info_focus: list[str] = []
    bio: str | None = None


@router.post("/auth/profile")
async def update_profile(request: Request, body: ProfileRequest):
    user_id = _verify_token(request.headers.get("Authorization", ""))
    engine = request.app.state.engine
    async with engine.begin() as conn:
        await conn.execute(
            text("""
                UPDATE users
                SET school = :school, major = :major,
                    enrollment_status = :enrollment_status::enrollment_status,
                    grade = :grade::grade_level,
                    info_focus = :info_focus,
                    bio = :bio
                WHERE id = :user_id
            """),
            {
                "school": body.school,
                "major": body.major,
                "enrollment_status": body.enrollment_status,
                "grade": body.grade,
                "info_focus": body.info_focus,
                "bio": body.bio,
                "user_id": user_id,
            },
        )
    return {"status": "ok"}

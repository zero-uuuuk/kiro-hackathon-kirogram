"""User profile endpoints."""

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import text

from api.models import UserCreate, UserUpdate, UserResponse

router = APIRouter()


def _row_to_response(r) -> UserResponse:
    return UserResponse(
        id=r["id"], email=r["email"], name=r["name"],
        school=r["school"], major=r["major"],
        enrollment_status=r["enrollment_status"], grade=r["grade"],
        info_focus=list(r["info_focus"] or []), bio=r["bio"],
        created_at=r["created_at"],
    )


@router.post("/users", response_model=UserResponse, status_code=201)
async def create_user(request: Request, body: UserCreate):
    engine = request.app.state.engine
    stmt = text("""
        INSERT INTO users (email, name, school, major, enrollment_status, grade, info_focus, bio)
        VALUES (:email, :name, :school, :major, :enrollment_status, :grade, :info_focus, :bio)
        RETURNING id, email, name, school, major, enrollment_status::text, grade::text, info_focus, bio, created_at
    """)
    async with engine.begin() as conn:
        row = (await conn.execute(stmt, {
            "email": body.email, "name": body.name,
            "school": body.school, "major": body.major,
            "enrollment_status": body.enrollment_status.value,
            "grade": body.grade.value,
            "info_focus": body.info_focus, "bio": body.bio,
        })).mappings().one()
    return _row_to_response(row)


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(request: Request, user_id: int):
    engine = request.app.state.engine
    stmt = text("""
        SELECT id, email, name, school, major, enrollment_status::text, grade::text, info_focus, bio, created_at
        FROM users WHERE id = :user_id
    """)
    async with engine.connect() as conn:
        row = (await conn.execute(stmt, {"user_id": user_id})).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return _row_to_response(row)


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(request: Request, user_id: int, body: UserUpdate):
    fields = {k: v for k, v in body.model_dump().items() if v is not None}
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    for key in ("enrollment_status", "grade"):
        if key in fields:
            fields[key] = fields[key].value if hasattr(fields[key], "value") else fields[key]

    set_clause = ", ".join(f"{k} = :{k}" for k in fields)
    fields["user_id"] = user_id
    stmt = text(f"""
        UPDATE users SET {set_clause} WHERE id = :user_id
        RETURNING id, email, name, school, major, enrollment_status::text, grade::text, info_focus, bio, created_at
    """)
    engine = request.app.state.engine
    async with engine.begin() as conn:
        row = (await conn.execute(stmt, fields)).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return _row_to_response(row)

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db import get_pool

router = APIRouter(prefix="/users", tags=["users"])


class UserCreate(BaseModel):
    email: str
    name: Optional[str] = None
    school: str
    major: str
    grade: str
    enrollment_status: str = "enrolled"
    interest_companies: list[str] = []
    interest_jobs: list[str] = []


class UserUpdate(BaseModel):
    email: Optional[str] = None
    name: Optional[str] = None
    school: Optional[str] = None
    major: Optional[str] = None
    grade: Optional[str] = None
    enrollment_status: Optional[str] = None
    interest_companies: Optional[list[str]] = None
    interest_jobs: Optional[list[str]] = None


@router.post("", status_code=201)
async def create_user(body: UserCreate):
    pool = await get_pool()
    row = await pool.fetchrow(
        """
        INSERT INTO users (email, name, school, major, grade, enrollment_status,
                           interest_companies, interest_jobs)
        VALUES ($1, $2, $3, $4, $5::grade_level, $6::enrollment_status, $7, $8)
        RETURNING *
        """,
        body.email, body.name, body.school, body.major,
        body.grade, body.enrollment_status,
        body.interest_companies, body.interest_jobs,
    )
    return dict(row)


@router.put("/{user_id}")
async def update_user(user_id: int, body: UserUpdate):
    fields = body.model_dump(exclude_none=True)
    if not fields:
        raise HTTPException(400, "No fields to update")

    set_clauses = []
    values = []
    for i, (col, val) in enumerate(fields.items(), start=1):
        cast = ""
        if col == "grade":
            cast = "::grade_level"
        elif col == "enrollment_status":
            cast = "::enrollment_status"
        set_clauses.append(f"{col} = ${i}{cast}")
        values.append(val)

    values.append(user_id)
    query = f"UPDATE users SET {', '.join(set_clauses)} WHERE id = ${len(values)} RETURNING *"

    pool = await get_pool()
    row = await pool.fetchrow(query, *values)
    if not row:
        raise HTTPException(404, "User not found")
    return dict(row)


@router.get("/{user_id}")
async def get_user(user_id: int):
    pool = await get_pool()
    row = await pool.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
    if not row:
        raise HTTPException(404, "User not found")
    return dict(row)

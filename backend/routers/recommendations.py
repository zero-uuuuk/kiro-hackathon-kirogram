"""POST/GET /users/{user_id}/recommendations — LLM 추천 생성 및 조회."""

import json

from fastapi import APIRouter, HTTPException
from pydantic_ai import Agent

from db import get_pool
from routers.jobs import matching_jobs

router = APIRouter()

rec_agent = Agent(
    "google-gla:gemini-2.0-flash",
    system_prompt=(
        "너는 취업 추천 도우미야. "
        "사용자 프로필과 채용공고 목록을 받으면, 각 공고에 대해 추천 이유와 준비할 일 목록을 생성해. "
        "반드시 아래 JSON 배열 형식으로만 응답해. 다른 텍스트는 포함하지 마.\n"
        '[{"job_posting_id": 123, "reason": "추천 이유", "todos": ["할 일1", "할 일2"]}]'
    ),
)


@router.post("/users/{user_id}/recommendations")
async def create_recommendations(user_id: int):
    pool = await get_pool()

    user = await pool.fetchrow("SELECT * FROM users WHERE id=$1", user_id)
    if not user:
        raise HTTPException(404, "User not found")

    jobs = await matching_jobs(user_id, top_n=10)
    if not jobs:
        return {"recommendations": []}

    user_profile = {
        "name": user["name"],
        "school": user["school"],
        "major": user["major"],
        "grade": user["grade"],
        "interest_companies": user["interest_companies"],
        "interest_jobs": user["interest_jobs"],
        "cv_summary": user["cv_summary"],
    }

    prompt = (
        f"사용자 프로필:\n{json.dumps(user_profile, ensure_ascii=False)}\n\n"
        f"채용공고 목록:\n{json.dumps(jobs, ensure_ascii=False)}\n\n"
        "각 공고에 대해 추천 이유와 준비할 일 목록을 JSON 배열로 생성해줘."
    )

    result = await rec_agent.run(prompt)
    raw = result.output.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3].strip()

    recs = json.loads(raw)

    for rec in recs:
        await pool.execute(
            """
            INSERT INTO ai_recommendations (user_id, job_posting_id, reason, todos)
            VALUES ($1, $2, $3, $4)
            """,
            user_id,
            rec["job_posting_id"],
            rec["reason"],
            json.dumps(rec["todos"], ensure_ascii=False),
        )

    return {"recommendations": recs}


@router.get("/users/{user_id}/recommendations")
async def get_recommendations(user_id: int):
    pool = await get_pool()

    user = await pool.fetchrow("SELECT id FROM users WHERE id=$1", user_id)
    if not user:
        raise HTTPException(404, "User not found")

    rows = await pool.fetch(
        """
        SELECT r.id, r.user_id, r.job_posting_id, r.reason, r.todos,
               r.relevance_score, r.is_read, r.created_at,
               j.title, j.company, j.end_date
        FROM ai_recommendations r
        JOIN job_postings j ON r.job_posting_id = j.id
        WHERE r.user_id = $1
        ORDER BY r.created_at DESC
        """,
        user_id,
    )

    return [dict(row) for row in rows]

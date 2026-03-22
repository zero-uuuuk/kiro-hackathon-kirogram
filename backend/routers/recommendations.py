"""POST/GET /users/{user_id}/recommendations — tool-calling Agent 기반 추천."""

import json

from fastapi import APIRouter, HTTPException
from pydantic_ai import Agent

from db import get_pool
from routers.jobs import matching_jobs

router = APIRouter()

rec_agent = Agent(
    "google-gla:gemini-3-flash-preview",
    system_prompt=(
        "너는 취업 추천 도우미 에이전트야. 반드시 아래 순서대로 도구를 호출해:\n"
        "1. get_user_profile 호출하여 사용자 프로필 획득\n"
        "2. get_matching_jobs 호출하여 매칭 공고 목록 획득\n"
        "중요: job_posting_id는 반드시 get_matching_jobs 결과에 있는 id 값만 사용해. 임의로 만들지 마.\n"
        "3. 각 공고마다:\n"
        "   a. analyze_weaknesses 호출 — 사용자 프로필과 공고를 비교하여 부족한 점(스킬/경험 갭)을 weaknesses 인자로 전달\n"
        "   b. collect_strengths 호출 — 사용자 프로필과 공고를 비교하여 이력서 강점(Fit)을 strengths 인자로 전달\n"
        "   c. 각 weakness마다 generate_improvement_plan 호출 — D-day 역산 준비일정을 todos 인자로 전달. "
        "각 todo는 {title: 할일 제목, offsetDays: 음수 정수(예: -14, -7, -3)} 형태여야 해\n"
        "4. 모든 공고 분석이 끝나면, 최종 결과를 아래 JSON 배열로만 응답해. 다른 텍스트 없이:\n"
        '[{"job_posting_id": 123, "reason": "종합 추천 이유", '
        '"strengths": ["강점1", "강점2"], '
        '"weaknesses": ["약점1", "약점2"], '
        '"todos": [{"title": "할일", "offsetDays": -14}]}]'
    ),
)


@rec_agent.tool_plain
async def get_user_profile(user_id: int) -> dict:
    """DB에서 사용자 프로필을 조회한다."""
    pool = await get_pool()
    row = await pool.fetchrow("SELECT * FROM users WHERE id=$1", user_id)
    if not row:
        return {"error": "User not found"}
    d = dict(row)
    for k, v in d.items():
        if hasattr(v, "isoformat"):
            d[k] = v.isoformat()
    return d


@rec_agent.tool_plain
async def get_matching_jobs(user_id: int, top_n: int = 10) -> list[dict]:
    """코사인 유사도 기반 매칭 공고 목록을 반환한다."""
    return await matching_jobs(user_id, top_n=top_n)


@rec_agent.tool_plain
def analyze_weaknesses(
    user_profile: str, job: str, weaknesses: list[str]
) -> list[str]:
    """사용자 프로필과 공고 간 갭 분석 결과를 수집한다. Agent가 분석한 weaknesses를 그대로 반환."""
    return weaknesses


@rec_agent.tool_plain
def collect_strengths(
    user_profile: str, job: str, strengths: list[str]
) -> list[str]:
    """사용자 프로필과 공고 간 강점(Fit) 분석 결과를 수집한다. Agent가 분석한 strengths를 그대로 반환."""
    return strengths


@rec_agent.tool_plain
def generate_improvement_plan(
    weakness: str, job_title: str, todos: list[dict]
) -> list[dict]:
    """약점 하나에 대한 D-day 역산 준비일정을 수집한다. 각 todo는 {title, offsetDays} 형태."""
    return todos


@router.post("/users/{user_id}/recommendations")
async def create_recommendations(user_id: int):
    pool = await get_pool()

    user = await pool.fetchrow("SELECT id FROM users WHERE id=$1", user_id)
    if not user:
        raise HTTPException(404, "User not found")

    # Get similarity scores before agent run
    jobs = await matching_jobs(user_id, top_n=10)
    score_map = {j["id"]: j["similarity_score"] for j in jobs}

    if not jobs:
        return {"recommendations": []}

    result = await rec_agent.run(
        f"user_id={user_id} 에 대해 추천을 생성해줘. 반드시 도구를 순서대로 호출해."
    )

    raw = result.output.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3].strip()

    try:
        recs = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(502, detail=f"Agent returned invalid JSON: {raw[:200]}")

    async with pool.acquire() as conn:
        async with conn.transaction():
            for rec in recs:
                job_id = rec["job_posting_id"]
                if job_id not in score_map:
                    print(f"WARNING: skipping hallucinated job_posting_id={job_id}")
                    continue
                await conn.execute(
                    """
                    INSERT INTO ai_recommendations
                        (user_id, job_posting_id, reason, todos, weaknesses, strengths, relevance_score)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (user_id, job_posting_id)
                    DO UPDATE SET reason = EXCLUDED.reason,
                                  todos = EXCLUDED.todos,
                                  weaknesses = EXCLUDED.weaknesses,
                                  strengths = EXCLUDED.strengths,
                                  relevance_score = EXCLUDED.relevance_score
                    """,
                    user_id,
                    job_id,
                    rec["reason"],
                    json.dumps(rec.get("todos", []), ensure_ascii=False),
                    json.dumps(rec.get("weaknesses", []), ensure_ascii=False),
                    json.dumps(rec.get("strengths", []), ensure_ascii=False),
                    score_map.get(job_id),
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
               r.weaknesses, r.strengths, r.relevance_score, r.is_read,
               r.created_at, j.title, j.company, j.end_date, j.source, j.url
        FROM ai_recommendations r
        JOIN job_postings j ON r.job_posting_id = j.id
        WHERE r.user_id = $1
        ORDER BY r.created_at DESC
        """,
        user_id,
    )

    return [dict(row) for row in rows]

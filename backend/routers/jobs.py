import os

import google.generativeai as genai
import numpy as np
from fastapi import APIRouter, HTTPException, Query

from db import get_pool

router = APIRouter()


def _embed(text: str) -> np.ndarray:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))
    res = genai.embed_content(model="models/text-embedding-004", content=text)
    return np.array(res["embedding"])


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    norm = np.linalg.norm(a) * np.linalg.norm(b)
    if norm == 0:
        return 0.0
    return float(np.dot(a, b) / norm)


@router.get("/users/{user_id}/matching-jobs")
async def matching_jobs(user_id: int, top_n: int = Query(default=10)):
    pool = await get_pool()

    user = await pool.fetchrow("SELECT * FROM users WHERE id=$1", user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    jobs = await pool.fetch("SELECT * FROM job_postings")
    if not jobs:
        return []

    parts = []
    if user["interest_companies"]:
        parts.append(" ".join(user["interest_companies"]))
    if user["interest_jobs"]:
        parts.append(" ".join(user["interest_jobs"]))
    if user["cv_summary"]:
        parts.append(user["cv_summary"])
    user_text = " ".join(parts) if parts else ""

    if not user_text.strip():
        return []

    user_vec = _embed(user_text)

    job_texts = [" ".join(filter(None, [j["title"], j["company"], j["key_info"]])) for j in jobs]
    valid = [(i, t) for i, t in enumerate(job_texts) if t.strip()]
    if not valid:
        return []
    indices, texts = zip(*valid)

    genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))
    batch_res = genai.embed_content(model="models/text-embedding-004", content=list(texts))
    job_vecs = [np.array(e) for e in batch_res["embedding"]]

    scored = []
    for idx, vec in zip(indices, job_vecs):
        job = jobs[idx]
        score = _cosine(user_vec, vec)
        scored.append({
            "id": job["id"],
            "title": job["title"],
            "company": job["company"],
            "start_date": str(job["start_date"]) if job["start_date"] else None,
            "end_date": str(job["end_date"]) if job["end_date"] else None,
            "key_info": job["key_info"],
            "source_filename": job["source_filename"],
            "similarity_score": round(score, 4),
        })

    scored.sort(key=lambda x: x["similarity_score"], reverse=True)
    return scored[:top_n]

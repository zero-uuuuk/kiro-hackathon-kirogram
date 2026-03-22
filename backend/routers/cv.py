"""POST /users/{user_id}/cv — CV 파싱 + AI 정제 + DB 저장."""

import io
import re

import httpx
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic_ai import Agent
from pypdf import PdfReader

from db import get_pool

router = APIRouter()

cv_agent = Agent(
    "google-gla:gemini-2.0-flash",
    system_prompt=(
        "너는 이력서 정제 도우미야. "
        "주어진 이력서 원문에서 핵심 정보(기술스택, 경력, 학력, 프로젝트)만 "
        "간결하게 정리해서 한국어로 반환해. 불필요한 서식이나 안내문구는 제거해."
    ),
)


def _strip_html(html: str) -> str:
    return re.sub(r"<[^>]+>", "", html)


async def _extract_from_url(url: str) -> str:
    async with httpx.AsyncClient(follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
    return _strip_html(resp.text)


def _extract_from_pdf(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


@router.post("/users/{user_id}/cv")
async def upload_cv(
    user_id: int,
    file: UploadFile | None = File(None),
    url: str | None = Form(None),
):
    if not file and not url:
        raise HTTPException(400, "file 또는 url 중 하나를 제출하세요.")

    pool = await get_pool()

    row = await pool.fetchrow("SELECT id FROM users WHERE id = $1", user_id)
    if not row:
        raise HTTPException(404, "사용자를 찾을 수 없습니다.")

    if url:
        raw_text = await _extract_from_url(url)
        result = await cv_agent.run(raw_text)
        await pool.execute(
            "UPDATE users SET cv_summary = $1, resume_url = $2 WHERE id = $3",
            result.output, url, user_id,
        )
        return {"cv_summary": result.output, "resume_url": url}

    data = await file.read()
    raw_text = _extract_from_pdf(data)
    result = await cv_agent.run(raw_text)
    await pool.execute(
        "UPDATE users SET cv_summary = $1, resume_filename = $2 WHERE id = $3",
        result.output, file.filename, user_id,
    )
    return {"cv_summary": result.output, "resume_filename": file.filename}

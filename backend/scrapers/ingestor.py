"""수집된 로컬 파일을 읽어 job_postings 테이블에 INSERT하는 Agent."""

import json
import re
from datetime import date

from pydantic_ai import Agent
from pydantic_ai.tools import RunContext

from config import SAMSUNG_JOBS_DIR, CJ_JOBS_DIR
from db import get_pool

agent = Agent(
    "google-gla:gemini-3-flash-preview",
    system_prompt=(
        "너는 채용공고 데이터 정제 및 DB 저장 에이전트야.\n"
        "read_samsung_jobs 툴로 삼성 공고 목록을 받고 각 항목마다 upsert_job_posting 툴로 저장해.\n"
        "read_cj_jobs 툴로 CJ 파일 목록을 받고, 각 파일마다 analyze_cj_job_image 툴로 분석한 뒤 upsert_job_posting 툴로 저장해.\n"
        "날짜 형식은 YYYY-MM-DD로 변환해. 없으면 null로 둬."
    ),
)


def _parse_samsung_date(raw: str) -> str | None:
    """'202603191000' → '2026-03-19'"""
    m = re.match(r"(\d{4})(\d{2})(\d{2})", raw or "")
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else None


@agent.tool_plain
def read_samsung_jobs() -> list[dict]:
    """samsung_jobs/ 디렉토리의 JSON 파일을 읽어 공고 목록을 반환한다."""
    results = []
    for f in SAMSUNG_JOBS_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            results.append({
                "source": "samsung",
                "source_filename": f.name,
                "title": data.get("title", ""),
                "company": data.get("company", ""),
                "start_date": _parse_samsung_date(data.get("startdate", "")),
                "end_date": _parse_samsung_date(data.get("enddate", "")),
                "key_info": "\n".join(filter(None, [
                    data.get("intro", ""),
                    data.get("jobs", ""),
                    data.get("step", ""),
                ])),
            })
        except Exception:
            pass
    print(f"[read_samsung_jobs] {len(results)}개 로드")
    return results


@agent.tool_plain
def read_cj_jobs() -> list[dict]:
    """cj_jobs/ 디렉토리의 JPG 파일 목록을 반환한다 (파일명만)."""
    results = [
        {"source": "cj", "source_filename": f.name}
        for f in CJ_JOBS_DIR.glob("*.jpg")
    ]
    print(f"[read_cj_jobs] {len(results)}개 로드")
    return results


@agent.tool
async def analyze_cj_job_image(_ctx, source_filename: str) -> dict:
    """CJ JPG 이미지를 분석하여 title, company, key_info를 추출한다."""
    import google.generativeai as genai
    import os as _os
    print(f"[analyze_cj_job_image] 분석 중: {source_filename}")
    genai.configure(api_key=_os.environ["GEMINI_API_KEY"])
    img_bytes = (CJ_JOBS_DIR / source_filename).read_bytes()
    model = genai.GenerativeModel("gemini-3-flash-preview")
    response = model.generate_content([
        "이 채용공고 이미지에서 다음 정보를 JSON으로 추출해줘: title(공고 제목), company(회사명), key_info(직무요건 요약, 200자 이내). 반드시 JSON만 반환해.",
        {"mime_type": "image/jpeg", "data": img_bytes},
    ])
    import json as _json, re as _re
    text = response.text.strip()
    m = _re.search(r'\{.*\}', text, _re.DOTALL)
    if not m:
        raise ValueError(f"LLM did not return JSON for {source_filename}: {text[:100]}")
    parsed = _json.loads(m.group())
    result = {
        "source_filename": source_filename,
        "title": parsed.get("title", ""),
        "company": parsed.get("company", "CJ"),
        "key_info": parsed.get("key_info", ""),
    }
    print(f"  → title={result['title']!r}, company={result['company']!r}")
    return result


@agent.tool
async def upsert_job_posting(
    _ctx,
    title: str,
    company: str,
    source_filename: str,
    key_info: str = "",
    start_date: str | None = None,
    end_date: str | None = None,
    source: str = "",
    url: str = "",
) -> str:
    """job_postings 테이블에 공고를 upsert한다. source_filename 기준 중복 방지."""
    print(f"[upsert_job_posting] {source_filename} | {company} | {title!r}")
    pool = await get_pool()

    def _to_date(s: str | None) -> date | None:
        if not s:
            return None
        try:
            return date.fromisoformat(s)
        except ValueError:
            return None

    await pool.execute(
        """
        INSERT INTO job_postings (title, company, start_date, end_date, key_info, source_filename, source, url)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        ON CONFLICT (source_filename) DO UPDATE
            SET title=$1, company=$2, start_date=$3, end_date=$4, key_info=$5,
                source = EXCLUDED.source, url = EXCLUDED.url
        """,
        title, company, _to_date(start_date), _to_date(end_date), key_info, source_filename, source, url,
    )
    print(f"  → DB upsert 완료: {source_filename}")
    return f"upserted: {source_filename}"


async def ingest_to_db() -> None:
    """수집된 로컬 파일을 읽어 job_postings에 저장한다."""
    await agent.run(
        "read_samsung_jobs 툴로 삼성 공고를 읽고 각각 upsert_job_posting으로 저장해. "
        "그 다음 read_cj_jobs 툴로 CJ 파일 목록을 받아 각 파일마다 analyze_cj_job_image로 분석한 뒤 "
        "upsert_job_posting으로 저장해. 확인 없이 바로 실행해."
    )

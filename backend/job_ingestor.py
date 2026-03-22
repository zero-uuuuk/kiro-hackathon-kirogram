"""수집된 로컬 파일을 읽어 job_postings 테이블에 INSERT하는 Agent."""

import json
import os
import re
from datetime import date
from pathlib import Path

import httpx
from dotenv import load_dotenv
from google import genai as google_genai
from google.genai import types as genai_types
from pydantic_ai import Agent

from db import get_pool

load_dotenv()

SAMSUNG_JOBS_DIR = Path(__file__).parent / "storage" / "samsung_jobs"
DOWNLOADS_DIR = Path(__file__).parent / "storage" / "cj_jobs"
CJ_DETAIL_URL = "https://recruit.cj.net/recruit/ko/recruit/recruit/detail.fo?zz_jo_num={}"

agent = Agent(
    "google-gla:gemini-3-flash-preview",
    system_prompt=(
        "너는 채용공고 데이터 정제 및 DB 저장 에이전트야.\n"
        "read_samsung_jobs 툴로 삼성 공고 목록을 받고 각 항목마다 upsert_job_posting 툴로 저장해.\n"
        "read_cj_jobs 툴로 CJ 파일 목록을 받고, 각 파일마다 analyze_cj_job_image 툴로 분석한 뒤 upsert_job_posting 툴로 저장해.\n"
        "날짜 형식은 YYYY-MM-DD로 변환해. 없으면 null로 둬."
    ),
)

_genai_client = None

def _get_genai_client():
    global _genai_client
    if _genai_client is None:
        _genai_client = google_genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    return _genai_client


def _parse_samsung_date(raw: str) -> str | None:
    m = re.match(r"(\d{4})(\d{2})(\d{2})", raw or "")
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else None


@agent.tool_plain
def read_samsung_jobs() -> list[dict]:
    """storage/samsung_jobs/ 디렉토리의 JSON 파일을 읽어 공고 목록을 반환한다."""
    results = []
    for f in SAMSUNG_JOBS_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            # key_info: 모든 필드 최대한 상세하게
            key_info_parts = []
            if data.get("intro"):
                key_info_parts.append(f"[회사소개]\n{data['intro']}")
            if data.get("jobs"):
                key_info_parts.append(f"[직무상세]\n{data['jobs']}")
            if data.get("step"):
                key_info_parts.append(f"[전형일정]\n{data['step']}")
            if data.get("process"):
                key_info_parts.append(f"[지원방법]\n{data['process']}")
            if data.get("attachment"):
                key_info_parts.append(f"[제출서류]\n{data['attachment']}")
            results.append({
                "source_filename": f.name,
                "title": data.get("title", ""),
                "company": data.get("company", ""),
                "start_date": _parse_samsung_date(data.get("startdate", "")),
                "end_date": _parse_samsung_date(data.get("enddate", "")),
                "key_info": "\n\n".join(key_info_parts),
            })
        except Exception:
            pass
    print(f"[read_samsung_jobs] {len(results)}개 로드")
    return results


@agent.tool_plain
def read_cj_jobs() -> list[dict]:
    """storage/cj_jobs/ 디렉토리의 JPG 파일 목록을 반환한다 (파일명만)."""
    results = [{"source_filename": f.name} for f in DOWNLOADS_DIR.glob("*.jpg")]
    print(f"[read_cj_jobs] {len(results)}개 로드")
    return results


async def _fetch_cj_dates(zz_jo_num: str) -> tuple[str | None, str | None]:
    """CJ 상세 페이지에서 시작/마감일을 텍스트로 추출한다."""
    url = CJ_DETAIL_URL.format(zz_jo_num)
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            text = resp.text
        # 날짜 패턴: YYYY.MM.DD 또는 YYYY-MM-DD
        dates = re.findall(r'(\d{4})[.\-](\d{2})[.\-](\d{2})', text)
        if len(dates) >= 2:
            start = f"{dates[0][0]}-{dates[0][1]}-{dates[0][2]}"
            end = f"{dates[1][0]}-{dates[1][1]}-{dates[1][2]}"
            return start, end
        elif len(dates) == 1:
            return None, f"{dates[0][0]}-{dates[0][1]}-{dates[0][2]}"
    except Exception as e:
        print(f"  [WARN] CJ 날짜 fetch 실패 ({zz_jo_num}): {e}")
    return None, None


@agent.tool
async def analyze_cj_job_image(_ctx, source_filename: str) -> dict:
    """CJ JPG 이미지를 분석하여 title, company, key_info, start_date, end_date를 추출한다."""
    print(f"[analyze_cj_job_image] 분석 중: {source_filename}")
    client = _get_genai_client()
    img_bytes = (DOWNLOADS_DIR / source_filename).read_bytes()
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=[
            (
                "이 채용공고 이미지에서 다음 정보를 JSON으로 추출해줘:\n"
                "- title: 공고 제목\n"
                "- company: 회사명\n"
                "- key_info: 직무 소개, 담당업무, 자격요건, 우대사항, 복리후생, 전형절차 등 모든 내용을 최대한 상세하게\n"
                "- start_date: 지원 시작일 (YYYY-MM-DD, 없으면 null)\n"
                "- end_date: 지원 마감일 (YYYY-MM-DD, 없으면 null)\n"
                "반드시 JSON만 반환해."
            ),
            genai_types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"),
        ],
    )
    text = response.text.strip()
    m = re.search(r'\{.*\}', text, re.DOTALL)
    parsed = json.loads(m.group()) if m else {}

    start_date = parsed.get("start_date")
    end_date = parsed.get("end_date")

    # 마감일 없으면 웹페이지에서 추출
    if not end_date:
        zz_jo_num = source_filename.replace(".jpg", "")
        print(f"  [WARN] end_date 없음 → 웹페이지 fallback: {zz_jo_num}")
        start_date, end_date = await _fetch_cj_dates(zz_jo_num)

    result = {
        "source_filename": source_filename,
        "title": parsed.get("title", ""),
        "company": parsed.get("company", "CJ"),
        "key_info": parsed.get("key_info", ""),
        "start_date": start_date,
        "end_date": end_date,
    }
    print(f"  -> title={result['title']!r}, end_date={result['end_date']!r}")
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
) -> str:
    """job_postings 테이블에 공고를 upsert한다. source_filename 기준 중복 방지."""
    print(f"[upsert_job_posting] {source_filename} | {company} | {title!r} | end={end_date}")
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
        INSERT INTO job_postings (title, company, start_date, end_date, key_info, source_filename)
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (source_filename) DO UPDATE
            SET title=$1, company=$2, start_date=$3, end_date=$4, key_info=$5
        """,
        title, company, _to_date(start_date), _to_date(end_date), key_info, source_filename,
    )
    print(f"  -> DB upsert 완료: {source_filename}")
    return f"upserted: {source_filename}"


async def ingest_to_db() -> None:
    """수집된 로컬 파일을 읽어 job_postings에 저장한다."""
    print("[ingest_to_db] 시작")
    await agent.run(
        "read_samsung_jobs 툴로 삼성 공고를 읽고 각각 upsert_job_posting으로 저장해. "
        "그 다음 read_cj_jobs 툴로 CJ 파일 목록을 받아 각 파일마다 analyze_cj_job_image로 분석한 뒤 "
        "upsert_job_posting으로 저장해. 확인 없이 바로 실행해."
    )
    print("[ingest_to_db] 완료")

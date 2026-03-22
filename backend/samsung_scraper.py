"""삼성 채용공고 스크래퍼 — pydantic-ai Agent 기반."""

import json
import re
from pathlib import Path

import httpx
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from pydantic_ai import Agent

load_dotenv()

SAMSUNG_JOBS_DIR = Path(__file__).parent / "samsung_jobs"
LIST_URL = "https://www.samsungcareers.com/hr/"
DETAIL_URL = "https://www.samsungcareers.com/recruit/detail.data"

agent = Agent(
    "google-gla:gemini-2.0-flash",
    system_prompt=(
        "너는 채용공고 텍스트 정제 도우미야. "
        "scrape_job_detail 툴로 원본 텍스트를 받으면 다음 노이즈를 제거해:\n"
        "- HTML 태그 (<br>, <p>, &nbsp; 등)\n"
        "- 중복 공백 및 불필요한 줄바꿈\n"
        "- 홈페이지 URL, 로그인 안내문구 등 무관한 안내문\n"
        "- 특수문자 남용 (★, ●, ■ 등 반복)\n"
        "정제 후 save_job_json 툴로 저장해."
    ),
)


@agent.tool_plain
async def collect_seqno_list() -> list[str]:
    """리스트 페이지에서 /hr/list.data 응답을 인터셉트하여 seqno 목록을 반환한다."""
    html_body = ""

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        async def on_response(response):
            nonlocal html_body
            if "/hr/list.data" in response.url:
                try:
                    html_body = await response.text()
                except Exception:
                    pass

        page.on("response", on_response)
        await page.goto(LIST_URL, wait_until="networkidle")
        await browser.close()

    raw = re.findall(r'data-value="([\d,]+)"', html_body)
    return list(dict.fromkeys(v.replace(",", "") for v in raw))


@agent.tool_plain
async def scrape_job_detail(seqno: str) -> str:
    """detail.data API를 호출하여 공고 원본 텍스트를 반환한다 (노이즈 제거 전)."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(DETAIL_URL, params={"seqno": seqno, "strCode": ""})
        resp.raise_for_status()
        body = resp.json()
        data = body.get("data") or {}
        result = data.get("result") or {}
        items = data.get("items") or []

    jobs_text = ""
    for item in items:
        jobs_text += f"\n[직무: {item.get('titleKr', '')}]\n"
        jobs_text += f"수행업무: {item.get('taskKr', '')}\n"
        jobs_text += f"지원자격: {item.get('qlfctKr', '')}\n"
        jobs_text += f"우대사항: {item.get('favorKr', '')}\n"

    fields = {
        "seqno": seqno,
        "title": result.get("title", ""),
        "company": result.get("cmpNameKr", ""),
        "startdate": result.get("startdate", ""),
        "enddate": result.get("enddate", ""),
        "intro": result.get("introKr", ""),
        "jobs": jobs_text.strip(),
        "step": result.get("stepKr", ""),
        "process": result.get("processKr", ""),
        "attachment": result.get("attachmentKr", ""),
    }
    return "\n".join(f"{k}: {v}" for k, v in fields.items())


@agent.tool_plain
def save_job_json(seqno: str, title: str, company: str, startdate: str, enddate: str,
                  intro: str, jobs: str, step: str, process: str, attachment: str) -> str:
    """정제된 공고 데이터를 JSON 파일로 저장하고 저장 경로를 반환한다."""
    SAMSUNG_JOBS_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "seqno": seqno, "title": title, "company": company,
        "startdate": startdate, "enddate": enddate,
        "intro": intro, "jobs": jobs, "step": step,
        "process": process, "attachment": attachment,
    }
    save_path = SAMSUNG_JOBS_DIR / f"{seqno}.json"
    save_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(save_path)


def main() -> None:
    result = agent.run_sync(
        "collect_seqno_list 툴로 seqno 목록을 수집하고, "
        "각 seqno마다 scrape_job_detail 툴로 원본 텍스트를 가져온 뒤 "
        "노이즈를 제거하고 save_job_json 툴로 저장해줘. 확인 없이 바로 실행해."
    )
    print(result.output)


if __name__ == "__main__":
    main()

"""CJ 채용공고 JPG 스크래퍼 — pydantic-ai Agent 기반."""

from pathlib import Path
from urllib.parse import urljoin

import httpx
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from pydantic_ai import Agent

load_dotenv()

DOWNLOADS_DIR = Path(__file__).parent / "downloads"
LIST_URL = "https://recruit.cj.net/recruit/ko/recruit/recruit/list.fo"
DETAIL_BASE = "https://recruit.cj.net/recruit/ko/recruit/recruit/detail.fo"
RECRUIT_BASE = "https://recruit.cj.net"

agent = Agent("google-gla:gemini-2.0-flash")


@agent.tool_plain
async def collect_job_list() -> list[str]:
    """리스트 페이지 API 응답에서 모든 공고의 zz_jo_num 목록을 수집한다."""
    nums: list[str] = []
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        async def on_response(response):
            if "searchNewGonggoList" in response.url:
                try:
                    data = await response.json()
                    for item in data.get("ds_newRecruitList") or []:
                        num = str(item.get("zz_jo_num", ""))
                        if num and num not in nums:
                            nums.append(num)
                except Exception:
                    pass

        page.on("response", on_response)
        await page.goto(LIST_URL, wait_until="networkidle")
        await browser.close()
    return nums


@agent.tool_plain
async def download_job_jpg(zz_jo_num: str) -> str:
    """상세 페이지에서 공고 JPG 이미지를 다운로드하여 저장 경로를 반환한다."""
    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
    jpg_url: str | None = None

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(f"{DETAIL_BASE}?zz_jo_num={zz_jo_num}", wait_until="networkidle")
        img = await page.query_selector('img[src*="/recnfs/"]')
        if img:
            src = await img.get_attribute("src") or ""
            jpg_url = src if src.startswith("http") else urljoin(RECRUIT_BASE, src)
        await browser.close()

    if not jpg_url:
        return f"No JPG found for {zz_jo_num}"

    save_path = DOWNLOADS_DIR / f"{zz_jo_num}.jpg"
    async with httpx.AsyncClient() as client:
        resp = await client.get(jpg_url)
        resp.raise_for_status()
        save_path.write_bytes(resp.content)
    return str(save_path)


def main() -> None:
    result = agent.run_sync(
        "collect_job_list 툴로 공고 목록을 수집하고, 각 zz_jo_num마다 download_job_jpg 툴을 호출해서 JPG를 모두 다운로드해줘. 확인 없이 바로 실행해."
    )
    print(result.output)


if __name__ == "__main__":
    main()

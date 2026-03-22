"""
Two-agent crawler:
  Agent1 (CrawlerCodeAgent): URL을 받아 해당 사이트 전용 크롤러 코드를 생성 → crawler/generated/<slug>.py 저장
  Agent2 (RunnerAgent): 생성된 코드를 실행 → 결과 검증 → 실패 시 Agent1에 재작성 지시 → 성공 시 DB 저장
"""

import argparse
import asyncio
import json
import logging
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

import boto3
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

load_dotenv()

logger = logging.getLogger(__name__)

# ── Bedrock 클라이언트 ──────────────────────────────────────────────────────────
_client = boto3.client(
    "bedrock-runtime",
    region_name=os.environ["AWS_DEFAULT_REGION"],
    aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
)
MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "amazon.nova-micro-v1:0")

GENERATED_DIR = Path(__file__).parent / "generated"
MAX_RETRIES = 3

# ── DB ─────────────────────────────────────────────────────────────────────────
def _get_engine():
    url = os.environ["DATABASE_URL"].replace("postgresql://", "postgresql+asyncpg://", 1)
    return create_async_engine(url)

async def _upsert_post(engine, post: dict):
    async with engine.begin() as conn:
        await conn.execute(text("""
            INSERT INTO posts (title, company, deadline, description, url, source_site, category, raw_content, created_at, updated_at)
            VALUES (:title, :company, :deadline, :description, :url, :source_site, :category, :raw_content, NOW(), NOW())
            ON CONFLICT (url) DO UPDATE SET
                title = EXCLUDED.title,
                company = EXCLUDED.company,
                deadline = EXCLUDED.deadline,
                description = EXCLUDED.description,
                raw_content = EXCLUDED.raw_content,
                updated_at = NOW()
        """), post)

# ── 코드 추출 ──────────────────────────────────────────────────────────────────
def _extract_code(text: str) -> str:
    """LLM 응답에서 Python 코드만 추출."""
    text = text.strip()
    if "```" in text:
        parts = text.split("```")
        if len(parts) >= 2:
            code = parts[1]
            if code.startswith("python"):
                code = code[6:]
            return code.strip()
    # 펜스 없으면 첫 import/from 줄부터
    for i, line in enumerate(text.splitlines()):
        if line.startswith("import ") or line.startswith("from "):
            return "\n".join(text.splitlines()[i:]).strip()
    return text.strip()

# ── Agent1: CrawlerCodeAgent ───────────────────────────────────────────────────
PROMPT_GENERATE = """\
다음 웹사이트를 크롤링하는 완전한 Python 스크립트를 작성해줘.

URL: {url}
Category: {category}

아래 HTML을 분석해서 공고/게시물 목록을 추출하는 코드를 작성해:

--- HTML ---
{html}
--- END ---

요구사항:
1. playwright sync_api만 사용 (asyncio 금지):
   from playwright.sync_api import sync_playwright
   with sync_playwright() as p:
       browser = p.chromium.launch(headless=True)
       page = browser.new_page()
       page.goto("{url}", timeout=30000, wait_until="networkidle")
       # 데이터 추출
       browser.close()

2. 결과를 stdout에 JSON 배열로 출력:
   [{{"title": "...", "company": null, "deadline": null, "description": "...", "url": "...", "category": "{category}"}}]

3. 에러 발생 시 [] 출력 후 종료 (exit code 0)
4. 외부 라이브러리는 playwright, httpx만 허용 (로컬 모듈 import 금지)
5. Python 코드만 출력 (설명 없이)
"""

PROMPT_RETRY = """\
이전 크롤러 스크립트가 실패했어. 아래 에러를 보고 수정된 코드를 작성해줘.

URL: {url}
Category: {category}

--- 에러 ---
{error}
--- END ---

--- 이전 HTML ---
{html}
--- END ---

요구사항 (반드시 준수):
1. playwright sync_api만 사용:
   from playwright.sync_api import sync_playwright
   with sync_playwright() as p:
       browser = p.chromium.launch(headless=True)
       page = browser.new_page()
       page.goto("{url}", timeout=30000, wait_until="networkidle")
       text = page.inner_text("body")
       browser.close()

2. 결과를 stdout에 JSON 배열로 출력
3. 에러 시 [] 출력 후 종료
4. Python 코드만 출력 (설명 없이)
"""

class CrawlerCodeAgent:
    def __init__(self):
        self._html: str | None = None

    async def _fetch_html(self, url: str) -> str:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, timeout=30000, wait_until="networkidle")
            html = await page.content()
            await browser.close()
        return html[:8000]

    def _call_llm(self, prompt: str) -> str:
        resp = _client.converse(
            modelId=MODEL_ID,
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": 4096},
        )
        return resp["output"]["message"]["content"][0]["text"]

    async def generate(self, url: str, category: str, error: str | None = None) -> Path:
        """크롤러 코드를 생성하고 파일 경로를 반환."""
        if self._html is None:
            logger.info("[Agent1] 페이지 HTML 수집: %s", url)
            self._html = await self._fetch_html(url)

        if error:
            logger.info("[Agent1] 에러 컨텍스트로 재생성 중...")
            prompt = PROMPT_RETRY.format(url=url, category=category, error=error, html=self._html)
        else:
            logger.info("[Agent1] 크롤러 코드 생성 중...")
            prompt = PROMPT_GENERATE.format(url=url, category=category, html=self._html)

        raw = self._call_llm(prompt)
        code = _extract_code(raw)

        # 파일 저장
        GENERATED_DIR.mkdir(exist_ok=True)
        slug = re.sub(r"[^a-z0-9]+", "_", urlparse(url).netloc.lower()).strip("_")
        file_path = GENERATED_DIR / f"{slug}_crawler.py"
        file_path.write_text(code, encoding="utf-8")
        logger.info("[Agent1] 파일 저장: %s", file_path)
        return file_path


# ── Agent2: RunnerAgent ────────────────────────────────────────────────────────
class RunnerAgent:
    async def run(self, url: str, category: str) -> int:
        """Agent1 → 실행 → 검증 → 실패 시 재시도 → DB 저장. 저장된 post 수 반환."""
        agent1 = CrawlerCodeAgent()
        engine = _get_engine()
        error_context = None

        try:
            for attempt in range(1, MAX_RETRIES + 1):
                logger.info("[Agent2] 시도 %d/%d", attempt, MAX_RETRIES)

                # Agent1에게 코드 생성 요청
                file_path = await agent1.generate(url, category, error=error_context)

                # 생성된 코드 실행
                logger.info("[Agent2] 실행: %s", file_path)
                try:
                    result = subprocess.run(
                        [sys.executable, str(file_path)],
                        capture_output=True, text=True, timeout=90,
                    )
                except subprocess.TimeoutExpired as e:
                    if e.process:
                        e.process.kill()
                    error_context = "스크립트가 90초 타임아웃으로 종료됨."
                    logger.warning("[Agent2] 타임아웃")
                    continue

                # 검증
                stderr_snippet = result.stderr[:1000] if result.stderr else ""
                stdout_snippet = result.stdout[:200] if result.stdout else ""

                if result.returncode != 0 or "Traceback" in result.stderr:
                    error_context = f"STDERR:\n{stderr_snippet}\nSTDOUT:\n{stdout_snippet}"
                    logger.warning("[Agent2] 실행 실패 → Agent1에 재작성 지시\n%s", stderr_snippet)
                    continue

                try:
                    posts = json.loads(result.stdout)
                    assert isinstance(posts, list) and len(posts) > 0
                    assert any(p.get("title") for p in posts)
                except (json.JSONDecodeError, AssertionError):
                    error_context = f"유효한 posts JSON이 아님. STDOUT:\n{stdout_snippet}"
                    logger.warning("[Agent2] 결과 검증 실패 → Agent1에 재작성 지시")
                    continue

                # 성공 → DB 저장
                logger.info("[Agent2] 검증 성공 — %d개 post 수집", len(posts))
                count = 0
                for post in posts:
                    if not post.get("title"):
                        continue
                    await _upsert_post(engine, {
                        "title": post.get("title"),
                        "company": post.get("company"),
                        "deadline": None,  # 문자열 deadline은 null 처리
                        "description": post.get("description"),
                        "url": post.get("url") or url,
                        "source_site": url,
                        "category": post.get("category") or category,
                        "raw_content": json.dumps(post, ensure_ascii=False)[:50000],
                    })
                    count += 1
                logger.info("[Agent2] DB 저장 완료: %d개", count)
                return count

            raise RuntimeError(f"최대 재시도 횟수({MAX_RETRIES}) 초과. 마지막 에러: {error_context}")
        finally:
            await engine.dispose()


# ── CLI ────────────────────────────────────────────────────────────────────────
async def _main():
    parser = argparse.ArgumentParser(description="Two-agent crawler: Agent1=코드생성, Agent2=실행+검증+DB저장")
    parser.add_argument("url", help="크롤링할 URL")
    parser.add_argument("--category", default="job", help="카테고리 (기본: job)")
    parser.add_argument("--run", action="store_true", help="Agent2까지 실행 (코드 생성 + 실행 + DB 저장)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if args.run:
        agent2 = RunnerAgent()
        count = await agent2.run(args.url, args.category)
        print(f"저장 완료: {count}개")
    else:
        agent1 = CrawlerCodeAgent()
        file_path = await agent1.generate(args.url, args.category)
        print(f"생성된 파일: {file_path}")


if __name__ == "__main__":
    asyncio.run(_main())

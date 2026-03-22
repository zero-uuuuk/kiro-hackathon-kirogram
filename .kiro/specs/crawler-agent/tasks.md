# Crawler Agent Tasks

## Task 1: Project Setup & Dependencies
- [x] 1.1: Create `backend/crawler/` package with `__init__.py`
- [x] 1.2: Create `backend/requirements.txt` with: playwright, boto3, sqlalchemy[asyncio], asyncpg, python-dotenv
- [x] 1.3: Create `backend/crawler/config.py` — load env vars (DATABASE_URL, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION)

## Task 2: Database Layer
- [x] 2.1: Create `backend/crawler/database.py` — async SQLAlchemy engine, posts table, crawl_runs table, upsert function
- [x] 2.2: Create DB init script that creates tables on first run

## Task 3: Page Fetcher
- [x] 3.1: Create `backend/crawler/fetcher.py` — Playwright async page fetcher with retry, rate limiting, returns HTML + text

## Task 4: Bedrock Extractor
- [x] 4.1: Create `backend/crawler/extractor.py` — listing page extraction (extract post URLs/titles from listing)
- [x] 4.2: Add detail page extraction (extract full structured post data from detail page)

## Task 5: Site Strategies
- [x] 5.1: Create `backend/crawler/strategies/base.py` — base strategy dataclass
- [x] 5.2: Create `backend/crawler/strategies/linkareer.py`
- [x] 5.3: Create `backend/crawler/strategies/wanted.py`
- [x] 5.4: Create `backend/crawler/strategies/saramin.py`
- [x] 5.5: Create `backend/crawler/strategies/devpost.py`
- [x] 5.6: Create `backend/crawler/strategies/dacon.py`

## Task 6: Orchestrator
- [x] 6.1: Create `backend/crawler/orchestrator.py` — main crawl loop: iterate strategies → fetch listings → extract links → fetch details → LLM extract → store
- [x] 6.2: Add crawl run tracking (start/end timestamps, posts_found count)

## Task 7: CLI Entry Point
- [x] 7.1: Create `backend/crawler/__main__.py` — CLI entry point with argparse (--site filter, --max-pages)

## Task 8: Media Processing (Image OCR & PDF Extraction)
- [x] 8.1: Update `backend/crawler/fetcher.py` — return `image_urls` and `attachment_urls` from detail pages
- [x] 8.2: Update `backend/crawler/orchestrator.py` — call MediaProcessor after fetching detail page, pass media context to `extract_detail`
- [x] 8.3: Update spec docs (requirements.md, design.md, tasks.md) to reflect media processing feature

## Task 9: Two-Agent Crawler (AnalyzerAgent + ExecutorAgent)
- [x] 9.1: Create `backend/crawler/analyze.py` — `CrawlStrategy` dataclass, `AnalysisError`, `AnalyzerAgent.analyze()`, `ExecutorAgent.execute()`
- [x] 9.2: Update `backend/crawler/extractor.py` — add `field_hints: dict | None = None` param to `extract_detail()`, inject hints into prompt
- [x] 9.3: Create `backend/crawler/analyze.py` `__main__` block — CLI: `python -m crawler.analyze <url> [--category] [--execute]`

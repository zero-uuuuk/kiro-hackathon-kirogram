# Crawler Agent Requirements

## R1: Two-Agent Architecture
- R1.1: The system must use two distinct agents: AnalyzerAgent and ExecutorAgent.
- R1.2: AnalyzerAgent receives a URL, analyzes the site's HTML structure using Bedrock Claude, and produces a `CrawlStrategy` (structured extraction plan with CSS hints and field mappings).
- R1.3: ExecutorAgent receives a `CrawlStrategy`, executes the crawl using Playwright, and stores results to PostgreSQL.
- R1.4: The two agents communicate via a `CrawlStrategy` dataclass (in-process, no queue needed).

## R2: AnalyzerAgent (Agent 1)
- R2.1: Accepts a target URL and optional category hint.
- R2.2: Fetches the page HTML via Playwright (JS-rendered).
- R2.3: Sends HTML structure (truncated to 8000 chars) to Bedrock Claude with a prompt asking for: listing link pattern, detail field selectors (title, company, deadline, description), and pagination pattern.
- R2.4: Returns a `CrawlStrategy` object with: `base_url`, `listing_url_pattern`, `max_pages`, `category`, `field_hints` (dict of CSS selectors or text patterns per field).
- R2.5: If analysis fails, raises `AnalysisError` with a descriptive message.

## R3: ExecutorAgent (Agent 2)
- R3.1: Accepts a `CrawlStrategy` produced by AnalyzerAgent.
- R3.2: Fetches listing pages using `listing_url_pattern` with Playwright.
- R3.3: Uses `field_hints` from the strategy to guide Bedrock detail extraction (passed as additional context in the prompt).
- R3.4: Stores extracted posts to PostgreSQL via existing `upsert_post`.
- R3.5: Returns count of stored posts.

## R4: Existing Capabilities Preserved
- R4.1: Existing `SiteStrategy`-based orchestration (`orchestrator.py`) must continue to work unchanged.
- R4.2: `extract_detail` in `extractor.py` must accept optional `field_hints: dict | None` parameter to incorporate strategy hints into the prompt.
- R4.3: Media processing (image OCR, PDF extraction) must remain functional.

## R5: Entry Points
- R5.1: `python -m crawler.analyze <url> [--category <cat>]` — runs AnalyzerAgent, prints strategy JSON.
- R5.2: `python -m crawler.analyze <url> [--category <cat>] --execute` — runs both agents end-to-end.
- R5.3: Existing `python -m crawler` CLI must remain unchanged.

# Crawler Agent Design

## Architecture Overview

```
CLI: python -m crawler.analyze <url> [--category <cat>] [--execute]
       ↓
  AnalyzerAgent.analyze(url, category) → CrawlStrategy
       ↓ (if --execute)
  ExecutorAgent.execute(strategy) → int (posts stored)
       ↓
  PostgreSQL (posts table)
```

Existing flow (unchanged):
```
python -m crawler [--site X] [--max-pages N]
       ↓
  CrawlerOrchestrator → SiteStrategy[] → PageFetcher → BedrockExtractor → PostgreSQL
```

## Components

### 1. CrawlStrategy (`crawler/analyze.py`)
Dataclass exchanged between agents:
```python
@dataclass
class CrawlStrategy:
    base_url: str
    listing_url_pattern: str   # e.g. "https://site.com/jobs?page={page}"
    max_pages: int
    category: str
    field_hints: dict          # e.g. {"title": "h1.job-title", "deadline": ".deadline"}
```

### 2. AnalyzerAgent (`crawler/analyze.py`)
- `analyze(url: str, category: str = "job") -> CrawlStrategy`
- Fetches page HTML via `fetch_page()` (Playwright).
- Sends HTML[:8000] to Bedrock Claude with structured analysis prompt.
- Prompt asks for: listing URL pattern, pagination pattern, CSS selectors for title/company/deadline/description.
- Parses JSON response into `CrawlStrategy`.
- Raises `AnalysisError` on failure.

### 3. ExecutorAgent (`crawler/analyze.py`)
- `execute(strategy: CrawlStrategy) -> int`
- Iterates `strategy.listing_url_pattern.format(page=N)` for N in 1..max_pages.
- Calls `fetch_page()` for each listing URL.
- Calls `extract_listing()` to get post URLs.
- Calls `fetch_page()` + `extract_detail(..., field_hints=strategy.field_hints)` for each detail URL.
- Upserts to DB via `upsert_post()`.
- Returns count of stored posts.

### 4. extractor.py update
- `extract_detail()` gains optional `field_hints: dict | None = None` parameter.
- When provided, appends field hints to the prompt as additional extraction guidance.

### 5. CLI (`crawler/analyze.py` as `__main__` module)
- `python -m crawler.analyze <url> [--category <cat>] [--execute]`
- Without `--execute`: prints `CrawlStrategy` as JSON.
- With `--execute`: runs both agents, prints count.

## Key Design Decisions

- D1: Both agents live in a single file `crawler/analyze.py` for simplicity.
- D2: `CrawlStrategy` is a plain dataclass — no serialization overhead for in-process use.
- D3: ExecutorAgent reuses existing `fetch_page`, `extract_listing`, `extract_detail`, `upsert_post` — no duplication.
- D4: `field_hints` are injected into the Bedrock prompt as a hint block, not enforced as hard selectors.
- D5: Existing `orchestrator.py` and `SiteStrategy` flow is untouched.

## Constraints
- C1: AWS credentials from environment variables.
- C2: DATABASE_URL from environment variable.
- C3: Model: `us.anthropic.claude-3-5-haiku-20241022-v1:0` via Bedrock `converse`.
- C4: No new dependencies — reuse existing `boto3`, `playwright`, `sqlalchemy`.

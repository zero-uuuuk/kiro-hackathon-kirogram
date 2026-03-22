# Two-Agent Dynamic Crawler Requirements

## R1: Agent1 — CodeGeneratorAgent
- R1.1: Accepts a URL and category. Fetches the page HTML via Playwright.
- R1.2: Sends HTML to Bedrock Claude with a prompt to generate a self-contained Python crawler script for that specific site.
- R1.3: The generated script must: fetch posts from the site, print results as JSON to stdout, and be runnable as `python <file>`.
- R1.4: Saves the generated script to `backend/crawler/generated/<site_slug>_crawler.py`.
- R1.5: Returns the file path of the generated script.
- R1.6: On retry, receives error context from Agent2 and regenerates the script with that context included in the prompt.

## R2: Agent2 — ValidatorAgent
- R2.1: Accepts the file path of a generated crawler script.
- R2.2: Executes the script via subprocess with a timeout (60s).
- R2.3: Parses stdout as JSON array of posts.
- R2.4: Validates: no exception in stderr, at least 1 post with a non-empty "title" field.
- R2.5: If validation fails, calls Agent1 again with the error context (stderr + stdout snippet).
- R2.6: Retries up to MAX_RETRIES (default 3) times before giving up.
- R2.7: On success, upserts all collected posts to DB via existing `upsert_post`.
- R2.8: Returns count of stored posts.

## R3: Generated Script Contract
- R3.1: The generated script is standalone — imports only stdlib + playwright + httpx.
- R3.2: Prints a JSON array to stdout: `[{"title": ..., "company": ..., "deadline": ..., "description": ..., "url": ..., "category": ...}, ...]`
- R3.3: Uses the DATABASE_URL / AWS env vars from environment if needed, but primarily just fetches and prints.

## R4: CLI
- R4.1: `python -m crawler.codegen <url> [--category <cat>]` — runs Agent1 only, prints generated file path.
- R4.2: `python -m crawler.codegen <url> [--category <cat>] --execute` — runs Agent1 → Agent2 loop, prints stored count.

## R5: Constraints
- R5.1: Generated files go to `backend/crawler/generated/` (create dir if not exists).
- R5.2: MAX_RETRIES = 3.
- R5.3: Reuse existing `upsert_post` from `crawler.database`.
- R5.4: No new dependencies.

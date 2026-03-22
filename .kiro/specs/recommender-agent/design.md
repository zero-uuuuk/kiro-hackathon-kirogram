# Recommender Agent Design

## Architecture Overview

```
Scheduler (APScheduler, daily)
       ↓
  RecommenderAgent.run(since)
       ↓
  ┌────────────────────┐
  │ Fetch posts (since)│  ← posts table
  └────────┬───────────┘
           ↓
  ┌────────────────────┐
  │ Batch fetch users  │  ← users table (batch size 50)
  └────────┬───────────┘
           ↓
  ┌────────────────────┐
  │ Bedrock Claude     │  ← per (user, post) pair
  │ relevance scoring  │
  └────────┬───────────┘
           ↓ (score >= 0.5)
  ┌────────────────────┐
  │ Upsert into        │  ← ai_recommendations table
  │ ai_recommendations │
  └────────────────────┘

Notification API (FastAPI)
  GET  /notifications   → unread recommendations
  POST /notifications/read → mark as read
```

## Components

### 1. RecommenderAgent (`backend/recommender/agent.py`)
- Entry point: `run(since: datetime) -> int` — returns count of stored recommendations.
- Fetches posts created after `since` from `posts` table.
- Iterates users in batches of `USER_BATCH_SIZE` (default 50).
- For each (user, post) pair, calls Bedrock Claude via `boto3.invoke_model`.
- Prompt includes user profile (school, major, grade, interests) and post data (title, company, category, deadline, description truncated to 3000 chars).
- Parses JSON response; stores if `relevance_score >= 0.5`.
- Upserts on `(user_id, post_id)` unique constraint.

### 2. Notification API (`backend/api/routes.py`)
- `GET /notifications?user_id=X`: Joins `ai_recommendations` with `posts`, filters `is_read = FALSE`, orders by `relevance_score DESC`.
- `POST /notifications/read`: Accepts `{user_id, post_ids}`, sets `is_read = TRUE`.
- FastAPI app (`backend/api/main.py`) manages async SQLAlchemy engine via lifespan.

### 3. Scheduler (`backend/scheduler.py`)
- APScheduler cron job at `CRAWL_SCHEDULE_HOUR` (default 9) in `Asia/Seoul` timezone.
- Runs crawler first, then `RecommenderAgent.run(since=utcnow - 25h)`.

## Database Schema References

### ai_recommendations
```sql
CREATE TABLE IF NOT EXISTS ai_recommendations (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    post_id         INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    reason          TEXT NOT NULL,
    todos           JSONB NOT NULL,
    relevance_score FLOAT,
    created_at      TIMESTAMP DEFAULT NOW(),
    is_read         BOOLEAN DEFAULT FALSE,
    UNIQUE (user_id, post_id)
);
```

### users
```sql
CREATE TABLE IF NOT EXISTS users (
    id          SERIAL PRIMARY KEY,
    email       TEXT UNIQUE NOT NULL,
    name        TEXT,
    school      TEXT NOT NULL,
    major       TEXT NOT NULL,
    grade       grade_level NOT NULL,
    interests   interest_category[] NOT NULL DEFAULT '{}',
    created_at  TIMESTAMP DEFAULT NOW()
);
```

## Key Design Decisions

- D1: Bedrock calls are offloaded to a thread executor (`run_in_executor`) since `boto3` is synchronous.
- D2: User batching (50) bounds memory usage for large user tables.
- D3: Upsert on `(user_id, post_id)` ensures idempotent re-runs without duplicate recommendations.
- D4: 25-hour lookback window in scheduler covers timing edge cases across daily runs.
- D5: Description truncated to 3000 chars to stay within token limits.

## Constraints
- C1: AWS credentials from environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION).
- C2: DATABASE_URL from environment variable.
- C3: Model: `us.anthropic.claude-3-5-haiku-20241022-v1:0` via Bedrock `invoke_model`.

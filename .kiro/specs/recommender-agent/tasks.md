# Recommender Agent Tasks

## Task 1: RecommenderAgent Core
- [x] 1.1: Create `backend/recommender/` package with `__init__.py`
- [x] 1.2: Create `backend/recommender/agent.py` — RecommenderAgent class with `run(since)` entry point
- [x] 1.3: Implement user batch fetching (`_fetch_users`) with configurable `USER_BATCH_SIZE`
- [x] 1.4: Implement post fetching (`_fetch_posts`) filtered by `created_at > since`
- [x] 1.5: Implement Bedrock Claude call (`_call_bedrock`) with structured prompt and JSON response parsing
- [x] 1.6: Implement upsert to `ai_recommendations` on `(user_id, post_id)` with reason, todos, relevance_score

## Task 2: Database Schema
- [x] 2.1: Add `ai_recommendations` table to `backend/schema.sql` with unique constraint on `(user_id, post_id)`
- [x] 2.2: Add `is_read` column to `ai_recommendations` for notification tracking

## Task 3: Notification API
- [x] 3.1: Create `backend/api/` package with `__init__.py`
- [x] 3.2: Create `backend/api/main.py` — FastAPI app with async SQLAlchemy engine lifespan
- [x] 3.3: Create `backend/api/routes.py` — `GET /notifications` returning unread recommendations ordered by relevance_score DESC
- [x] 3.4: Add `POST /notifications/read` endpoint to mark recommendations as read

## Task 4: Scheduler Integration
- [x] 4.1: Create `backend/scheduler.py` — APScheduler cron job at configurable hour (KST)
- [x] 4.2: Wire scheduler to run crawler then RecommenderAgent sequentially with 25h lookback

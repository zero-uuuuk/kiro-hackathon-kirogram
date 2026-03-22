# Recommender Agent Requirements

## R1: LLM-Based Matching
- R1.1: The system must use AWS Bedrock Claude (`us.anthropic.claude-3-5-haiku-20241022-v1:0`) to evaluate relevance between user profiles and crawled posts.
- R1.2: For each (user, post) pair the LLM must return: `reason` (Korean), `todos` (array of `{task, due}`), and `relevance_score` (0.0–1.0).
- R1.3: Only recommendations with `relevance_score >= 0.5` are stored.

## R2: Filtering Rules
- R2.1: Posts already recommended to a user (existing row in `ai_recommendations`) must be upserted, not duplicated.
- R2.2: Posts already marked as read (`is_read = TRUE`) must not be surfaced in notification queries.
- R2.3: Expired posts (`deadline < NOW()`) must not be included in notification results.

## R3: User Profile Input
- R3.1: User profiles are read from the `users` table with fields: `school`, `major`, `grade`, `interests`.
- R3.2: Users are processed in batches (batch size configurable, default 50).

## R4: Notification API
- R4.1: `GET /notifications?user_id=X` must return unread recommendations ordered by `relevance_score DESC`.
- R4.2: `POST /notifications/read` with `{user_id, post_ids}` must mark the specified recommendations as read.
- R4.3: Notification responses must include: `post_id`, `title`, `company`, `deadline`, `category`, `reason`, `todos`, `relevance_score`.

## R5: Scheduler Integration
- R5.1: The recommender must run daily after the crawler, triggered by the scheduler at a configurable hour (default 09:00 KST).
- R5.2: Each run processes posts created within the last 25 hours to account for timing overlap.

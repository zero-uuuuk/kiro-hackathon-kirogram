# Onboarding Backend Requirements

## R1: User Profile Schema
- R1.1: `school` (TEXT, required) — 학교명
- R1.2: `major` (TEXT, required) — 학과명
- R1.3: `enrollment_status` ENUM: `enrolled` | `leave_of_absence` | `graduated` — 재학상태 (required)
- R1.4: `grade` ENUM: `1` | `2` | `3` | `4` | `graduate` | `other` — 학년 (required)
- R1.5: `info_focus` TEXT[] — 정보 중심 다중선택 (예: spec_building, campus_info, job, hackathon, competition, scholarship). Replaces `interests interest_category[]`.
- R1.6: `bio` TEXT — 나에 대해 자유롭게 알려주기 (자연어, nullable)
- R1.7: `interest_category` ENUM type and `interests` column must be dropped/replaced.

## R2: Custom Sources (already exists, verify)
- R2.1: `custom_sources` table already has `url` + `description` (자연어). No change needed.

## R3: API Endpoints
- R3.1: `POST /users` — create user profile with new fields
- R3.2: `GET /users/{user_id}` — fetch user profile
- R3.3: `PATCH /users/{user_id}` — update user profile (partial)

## R4: Recommender Compatibility
- R4.1: `RecommenderAgent` uses user profile fields in Bedrock prompt. Must be updated to use `info_focus` + `bio` instead of `interests`.

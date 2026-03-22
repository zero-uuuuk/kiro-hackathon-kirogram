# Onboarding Backend Tasks

## Task 1: Schema Migration
- [x] 1.1: Update `backend/schema.sql` — drop `interest_category` ENUM, add `enrollment_status` ENUM, alter users table (add enrollment_status, info_focus, bio; remove interests)
- [x] 1.2: Create `backend/migrate_onboarding.py` — migration script: DROP TYPE interest_category CASCADE, CREATE TYPE enrollment_status, ALTER TABLE users ADD COLUMN enrollment_status/info_focus/bio

## Task 2: API Models
- [x] 2.1: Create `backend/api/models.py` — UserCreate, UserUpdate, UserResponse Pydantic models with EnrollmentStatus and GradeLevel enums

## Task 3: User API Endpoints
- [x] 3.1: Create `backend/api/user_routes.py` — POST /users, GET /users/{user_id}, PATCH /users/{user_id}
- [x] 3.2: Register user_routes in `backend/api/main.py`

## Task 4: Recommender Compatibility
- [x] 4.1: Update `backend/recommender/agent.py` — replace `interests` with `info_focus` + `bio` in Bedrock prompt

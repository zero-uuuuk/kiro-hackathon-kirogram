-- ============================================================
-- SchedAI Database Schema
-- ============================================================

-- 학년 ENUM
CREATE TYPE grade_level AS ENUM ('1', '2', '3', '4', 'graduate', 'other');

-- 재학 상태 ENUM
CREATE TYPE enrollment_status AS ENUM ('enrolled', 'leave_of_absence', 'graduated');

-- 1. Users
CREATE TABLE IF NOT EXISTS users (
    id                    SERIAL PRIMARY KEY,
    email                 TEXT UNIQUE NOT NULL,
    name                  TEXT,
    school                TEXT NOT NULL,            -- 학교 (필수)
    major                 TEXT NOT NULL,            -- 전공 (필수)
    enrollment_status     enrollment_status NOT NULL DEFAULT 'enrolled', -- 재학 상태
    grade                 grade_level NOT NULL,     -- 학년 (필수)
    info_focus            TEXT[] NOT NULL DEFAULT '{}',  -- 정보 중심 (다중선택)
    bio                   TEXT,                     -- 자기소개 (자유 입력)
    google_calendar_token JSONB,                    -- Google Calendar OAuth 토큰
    created_at            TIMESTAMP DEFAULT NOW()
);

-- 2. Posts (crawler-agent output)
CREATE TABLE IF NOT EXISTS posts (
    id          SERIAL PRIMARY KEY,
    title       TEXT NOT NULL,
    company     TEXT,
    deadline    TIMESTAMP,
    description TEXT,
    url         TEXT UNIQUE NOT NULL,
    source_site TEXT NOT NULL,
    category    TEXT NOT NULL,           -- job | hackathon | competition
    raw_content TEXT,
    created_at  TIMESTAMP DEFAULT NOW(),
    updated_at  TIMESTAMP DEFAULT NOW()
);

-- 3. Saved Posts (user ↔ post)
CREATE TABLE IF NOT EXISTS saved_posts (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    post_id     INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    saved_at    TIMESTAMP DEFAULT NOW(),
    UNIQUE (user_id, post_id)
);

-- 4. AI Recommendations
--    LLM이 공고 + 사용자 프로필 기반으로 생성한 추천 이유 및 할 일 목록
CREATE TABLE IF NOT EXISTS ai_recommendations (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    post_id         INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    reason          TEXT NOT NULL,       -- 추천 이유
    todos           JSONB NOT NULL,      -- 할 일 목록 (예: [{"task": "포트폴리오 준비", "due": "2026-04-01"}])
    relevance_score FLOAT,              -- 관련도 점수 (0.0 ~ 1.0)
    is_read         BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMP DEFAULT NOW(),
    UNIQUE (user_id, post_id)
);

-- 5. Calendar Events
--    사용자가 캘린더 등록을 선택한 공고
CREATE TABLE IF NOT EXISTS calendar_events (
    id                  SERIAL PRIMARY KEY,
    user_id             INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    post_id             INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    google_event_id     TEXT,            -- Google Calendar event ID (등록 후 저장)
    event_date          DATE NOT NULL,   -- D-day (기본: 공고 마감일)
    start_date          DATE,            -- Agent가 범위 일정 판단 시 시작일
    end_date            DATE,            -- Agent가 범위 일정 판단 시 종료일
    is_range            BOOLEAN DEFAULT FALSE,  -- FALSE: 단일 D-day / TRUE: 범위 일정
    is_registered       BOOLEAN DEFAULT FALSE,
    registered_at       TIMESTAMP,
    UNIQUE (user_id, post_id)
);

-- 6. Custom Sources (사용자가 등록한 관심 URL)
CREATE TABLE IF NOT EXISTS custom_sources (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    url             TEXT NOT NULL,
    description     TEXT,                -- 원하는 정보 설명 (예: "AI 관련 행사/밋업")
    last_crawled_at TIMESTAMP,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW(),
    UNIQUE (user_id, url)
);

-- 7. Crawl Runs (crawler-agent tracking)
CREATE TABLE IF NOT EXISTS crawl_runs (
    id          SERIAL PRIMARY KEY,
    site        TEXT NOT NULL,
    started_at  TIMESTAMP NOT NULL,
    finished_at TIMESTAMP,
    posts_found INTEGER DEFAULT 0,
    status      TEXT DEFAULT 'running'   -- running | done | failed
);

-- 8. Add is_read column to ai_recommendations for notification tracking
ALTER TABLE ai_recommendations ADD COLUMN IF NOT EXISTS is_read BOOLEAN DEFAULT FALSE;
-- ============================================================
-- SchedAI Database Schema
-- ============================================================

-- Reset
DROP TABLE IF EXISTS academic_notices CASCADE;
DROP TABLE IF EXISTS agent_sessions CASCADE;
DROP TABLE IF EXISTS job_postings CASCADE;
DROP TABLE IF EXISTS crawl_runs CASCADE;
DROP TABLE IF EXISTS custom_sources CASCADE;
DROP TABLE IF EXISTS calendar_events CASCADE;
DROP TABLE IF EXISTS ai_recommendations CASCADE;
DROP TABLE IF EXISTS saved_posts CASCADE;
DROP TABLE IF EXISTS posts CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TYPE IF EXISTS grade_level CASCADE;
DROP TYPE IF EXISTS enrollment_status CASCADE;

-- ENUMs
CREATE TYPE grade_level AS ENUM ('1', '2', '3', '4', 'graduate', 'other');
CREATE TYPE enrollment_status AS ENUM ('enrolled', 'leave_of_absence', 'graduated');

-- 1. Users
CREATE TABLE users (
    id                    SERIAL PRIMARY KEY,
    email                 TEXT UNIQUE NOT NULL,
    name                  TEXT,
    school                TEXT NOT NULL,
    major                 TEXT NOT NULL,
    enrollment_status     enrollment_status NOT NULL DEFAULT 'enrolled',
    grade                 grade_level NOT NULL,
    info_focus            TEXT[] NOT NULL DEFAULT '{}',
    bio                   TEXT,
    google_calendar_token JSONB,
    resume_filename       TEXT,
    resume_url            TEXT,
    interest_companies    TEXT[] NOT NULL DEFAULT '{}',
    interest_jobs         TEXT[] NOT NULL DEFAULT '{}',
    created_at            TIMESTAMP DEFAULT NOW()
);

-- 2. Posts (crawler-agent output)
CREATE TABLE posts (
    id          SERIAL PRIMARY KEY,
    title       TEXT NOT NULL,
    company     TEXT,
    deadline    TIMESTAMP,
    description TEXT,
    url         TEXT UNIQUE NOT NULL,
    source_site TEXT NOT NULL,
    category    TEXT NOT NULL,
    raw_content TEXT,
    created_at  TIMESTAMP DEFAULT NOW(),
    updated_at  TIMESTAMP DEFAULT NOW()
);

-- 3. Saved Posts
CREATE TABLE saved_posts (
    id       SERIAL PRIMARY KEY,
    user_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    post_id  INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    saved_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (user_id, post_id)
);

-- 4. AI Recommendations
CREATE TABLE ai_recommendations (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    post_id         INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    reason          TEXT NOT NULL,
    todos           JSONB NOT NULL,
    relevance_score FLOAT,
    is_read         BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMP DEFAULT NOW(),
    UNIQUE (user_id, post_id)
);

-- 5. Calendar Events
CREATE TABLE calendar_events (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    post_id         INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    google_event_id TEXT,
    event_date      DATE NOT NULL,
    start_date      DATE,
    end_date        DATE,
    is_range        BOOLEAN DEFAULT FALSE,
    is_registered   BOOLEAN DEFAULT FALSE,
    registered_at   TIMESTAMP,
    UNIQUE (user_id, post_id)
);

-- 6. Custom Sources
CREATE TABLE custom_sources (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    url             TEXT NOT NULL,
    description     TEXT,
    last_crawled_at TIMESTAMP,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW(),
    UNIQUE (user_id, url)
);

-- 7. Crawl Runs
CREATE TABLE crawl_runs (
    id          SERIAL PRIMARY KEY,
    site        TEXT NOT NULL,
    started_at  TIMESTAMP NOT NULL,
    finished_at TIMESTAMP,
    posts_found INTEGER DEFAULT 0,
    status      TEXT DEFAULT 'running'
);

-- 8. Job Postings
CREATE TABLE job_postings (
    id              SERIAL PRIMARY KEY,
    title           TEXT NOT NULL,
    company         TEXT NOT NULL,
    start_date      DATE,
    end_date        DATE,
    key_info        TEXT,
    source_filename TEXT,
    pinecone_id     TEXT UNIQUE,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- 9. Agent Sessions
CREATE TABLE agent_sessions (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER REFERENCES users(id) ON DELETE CASCADE,
    session_id  TEXT NOT NULL,
    agent_type  TEXT NOT NULL,
    messages    JSONB NOT NULL DEFAULT '[]',
    created_at  TIMESTAMP DEFAULT NOW(),
    updated_at  TIMESTAMP DEFAULT NOW()
);

-- 10. Academic Notices
CREATE TABLE academic_notices (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER REFERENCES users(id) ON DELETE CASCADE,
    title      TEXT NOT NULL,
    content    TEXT,
    source_url TEXT,
    keywords   TEXT[] NOT NULL DEFAULT '{}',
    category   TEXT,
    posted_at  TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (user_id, source_url)
);

-- 11. Schema extensions for profile & recommendation system
ALTER TABLE users ADD COLUMN IF NOT EXISTS cv_summary TEXT;
ALTER TABLE ai_recommendations ADD COLUMN IF NOT EXISTS job_posting_id INTEGER REFERENCES job_postings(id);
ALTER TABLE ai_recommendations ALTER COLUMN post_id DROP NOT NULL;
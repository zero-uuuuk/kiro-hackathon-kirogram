# Tasks: DB Schema 확장

## Task 1: users 테이블 확장
- [x] 1.1 `resume_filename TEXT` 컬럼 추가
- [x] 1.2 `resume_url TEXT` 컬럼 추가
- [x] 1.3 `interest_companies TEXT[] NOT NULL DEFAULT '{}'` 컬럼 추가
- [x] 1.4 `interest_jobs TEXT[] NOT NULL DEFAULT '{}'` 컬럼 추가

## Task 2: job_postings 테이블 생성
- [x] 2.1 `CREATE TABLE IF NOT EXISTS job_postings` 작성 (id, title, company, start_date, end_date, key_info, source_filename, pinecone_id, created_at)

## Task 3: agent_sessions 테이블 생성
- [x] 3.1 `CREATE TABLE IF NOT EXISTS agent_sessions` 작성 (id, user_id, session_id, agent_type, messages, created_at, updated_at)

## Task 4: academic_notices 테이블 생성
- [x] 4.1 `CREATE TABLE IF NOT EXISTS academic_notices` 작성 (id, user_id, title, content, source_url, keywords, category, posted_at, created_at)
- [x] 4.2 `UNIQUE (user_id, source_url)` 제약 추가

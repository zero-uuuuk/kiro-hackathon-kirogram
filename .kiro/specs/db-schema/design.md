# Design: DB Schema 확장

## 대상 파일
- `backend/schema.sql` — 기존 스키마에 추가/변경

## 변경 전략
- 기존 테이블(`users`)은 `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`로 확장한다.
- 신규 테이블은 `CREATE TABLE IF NOT EXISTS`로 추가한다.
- 기존 테이블(`posts`, `ai_recommendations` 등)은 건드리지 않는다.

## REQ-1: users 확장 컬럼

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `resume_filename` | TEXT | 업로드된 PDF 파일명 |
| `resume_url` | TEXT | 외부 이력서 URL 또는 S3 URL |
| `interest_companies` | TEXT[] DEFAULT '{}' | 관심 회사 목록 |
| `interest_jobs` | TEXT[] DEFAULT '{}' | 관심 직무 목록 |

## REQ-2: job_postings 테이블

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `id` | SERIAL PK | |
| `title` | TEXT NOT NULL | 채용공고 제목 |
| `company` | TEXT NOT NULL | 기업명 |
| `start_date` | DATE | 공고 시작일 |
| `end_date` | DATE | 공고 마감일 |
| `key_info` | TEXT | 핵심정보 (직무요건 요약) |
| `source_filename` | TEXT | 원본 파일명 (예: `{zz_jo_num}.jpg`) |
| `pinecone_id` | TEXT UNIQUE | Pinecone 벡터 ID |
| `created_at` | TIMESTAMP DEFAULT NOW() | |

## REQ-3: agent_sessions 테이블

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `id` | SERIAL PK | |
| `user_id` | INTEGER FK → users(id) | nullable (시스템 세션 허용) |
| `session_id` | TEXT NOT NULL | 대화 세션 식별자 |
| `agent_type` | TEXT NOT NULL | 예: `recommendation`, `calendar`, `filter` |
| `messages` | JSONB DEFAULT '[]' | `[{role, content, timestamp}]` |
| `created_at` | TIMESTAMP DEFAULT NOW() | |
| `updated_at` | TIMESTAMP DEFAULT NOW() | |

## REQ-4: academic_notices 테이블

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `id` | SERIAL PK | |
| `user_id` | INTEGER FK → users(id) ON DELETE CASCADE | |
| `title` | TEXT NOT NULL | 공지 제목 |
| `content` | TEXT | 본문 |
| `source_url` | TEXT | 원본 URL |
| `keywords` | TEXT[] DEFAULT '{}' | 매칭된 키워드 목록 |
| `category` | TEXT | 예: `scholarship`, `internship`, `event` |
| `posted_at` | TIMESTAMP | 원본 게시일 |
| `created_at` | TIMESTAMP DEFAULT NOW() | |
| UNIQUE | (user_id, source_url) | 중복 방지 |

## 불변 제약
- 기존 테이블 구조 변경 금지 (컬럼 삭제, 타입 변경, 이름 변경 불가).
- `pinecone_id`는 스키마에서 ID 보관만 담당. 실제 벡터 upsert는 애플리케이션 레이어 책임.

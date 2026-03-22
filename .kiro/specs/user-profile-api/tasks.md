# Tasks: 사용자 프로필 & 추천 시스템 API

## Task 0: 사전 준비
- [x] 0.1 `backend/schema.sql`에 `ALTER TABLE users ADD COLUMN IF NOT EXISTS cv_summary TEXT` 추가 및 DB 적용
- [x] 0.2 `ai_recommendations`에 `job_posting_id INTEGER REFERENCES job_postings(id)` 추가 및 DB 적용
- [x] 0.3 `requirements.txt`에 `google-generativeai`, `numpy`, `python-multipart` 추가
- [x] 0.4 `backend/db.py` 작성 (asyncpg 커넥션 풀, `get_pool()`)

## Task 1: 프로필 CRUD
- [x] 1.1 `backend/routers/users.py` — `POST /users` 구현
- [x] 1.2 `backend/routers/users.py` — `PUT /users/{user_id}` 구현 (partial update)
- [x] 1.3 `backend/routers/users.py` — `GET /users/{user_id}` 구현

## Task 2: CV 파싱
- [x] 2.1 `backend/routers/cv.py` — `POST /users/{user_id}/cv` 구현
  - URL 분기: httpx fetch → HTML 태그 strip → 텍스트 추출
  - PDF 분기: pypdf.PdfReader → 전 페이지 텍스트 concat
  - Pydantic AI Agent(gemini-2.0-flash)로 cv_summary 생성
  - DB UPDATE (cv_summary, resume_url or resume_filename)

## Task 3: 코사인 유사도 필터링
- [x] 3.1 `backend/routers/jobs.py` — `GET /users/{user_id}/matching-jobs?top_n=10` 구현
  - 사용자 쿼리 텍스트 조합 (interest_companies + interest_jobs + cv_summary)
  - Gemini text-embedding-004로 벡터화
  - job_postings 전체 로드 → 배치 벡터화 → numpy 코사인 유사도 → 상위 top_n 반환

## Task 4: LLM 추천
- [x] 4.1 `backend/routers/recommendations.py` — `POST /users/{user_id}/recommendations` 구현
  - matching-jobs 내부 호출
  - Pydantic AI Agent로 추천 이유 + todos 생성
  - UPSERT ai_recommendations (ON CONFLICT user_id, job_posting_id)
- [x] 4.2 `backend/routers/recommendations.py` — `GET /users/{user_id}/recommendations` 구현

## Task 5: 앱 진입점
- [x] 5.1 `backend/main.py` 작성 — FastAPI 앱 생성, 라우터 등록

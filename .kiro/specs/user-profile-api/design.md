# Design: 사용자 프로필 & 추천 시스템 API

## 파일 구조
```
backend/
  main.py          ← FastAPI 앱 진입점 (기존 없으면 신규)
  routers/
    users.py       ← REQ-1: 프로필 CRUD
    cv.py          ← REQ-2: CV 파싱 & 정제
    jobs.py        ← REQ-3: 코사인 유사도 필터링
    recommendations.py ← REQ-4: LLM 추천
  db.py            ← asyncpg 커넥션 풀
```

## DB 스키마 변경
- `users` 테이블에 `cv_summary TEXT` 컬럼 추가 (ALTER TABLE)
- `ai_recommendations` 테이블에 `job_posting_id INTEGER REFERENCES job_postings(id)` 추가

## REQ-1: 프로필 CRUD

**POST /users**
- Body: `{email, name, school, major, grade, enrollment_status, interest_companies[], interest_jobs[]}`
- INSERT INTO users → 생성된 row 반환

**PUT /users/{user_id}**
- Body: 위 필드 중 일부 (partial update)
- UPDATE users SET ... WHERE id = user_id

**GET /users/{user_id}**
- SELECT * FROM users WHERE id = user_id

## REQ-2: CV 파싱

**POST /users/{user_id}/cv**
- multipart/form-data: `file`(PDF) 또는 `url`(TEXT) 중 하나
- URL 처리: `httpx.AsyncClient().get(url)` → `response.text` (HTML strip)
- PDF 처리: `pypdf.PdfReader` → 전 페이지 텍스트 concat
- Agent: `pydantic_ai.Agent("google-gla:gemini-2.0-flash")` → 시스템 프롬프트로 핵심정보(기술스택, 경력, 학력, 프로젝트) 정제 요청
- UPDATE users SET cv_summary=..., resume_url=... / resume_filename=... WHERE id=user_id

## REQ-3: 코사인 유사도 필터링

**GET /users/{user_id}/matching-jobs?top_n=10**
- 사용자 쿼리 텍스트 = `interest_companies + interest_jobs + cv_summary` 합산
- `google.generativeai.embed_content(model="models/text-embedding-004", content=text)` 로 벡터화
- job_postings 전체 로드 → 각 공고 텍스트(title + company + key_info) 동일 방식 벡터화
- numpy로 코사인 유사도 계산 → 상위 top_n 반환

## REQ-4: LLM 추천

**POST /users/{user_id}/recommendations**
- REQ-3 matching-jobs 결과를 내부 호출로 획득
- Pydantic AI Agent에게 사용자 프로필 + 공고 목록 전달
- Agent 출력: `[{job_posting_id, reason, todos[]}]`
- UPSERT INTO ai_recommendations (user_id, job_posting_id, reason, todos)

**GET /users/{user_id}/recommendations**
- SELECT ai_recommendations JOIN job_postings WHERE user_id=user_id

## 의존성 추가
- `google-generativeai` — embedding API
- `numpy` — 코사인 유사도 계산
- `python-multipart` — FastAPI 파일 업로드

## 불변 제약
- 기존 테이블(posts, saved_posts 등) 구조 변경 금지
- ai_recommendations의 기존 post_id 컬럼은 nullable로 유지 (job_posting_id 신규 추가)

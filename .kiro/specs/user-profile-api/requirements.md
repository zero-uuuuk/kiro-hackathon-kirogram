# Requirements: 사용자 프로필 & 추천 시스템 API

## REQ-1: 사용자 프로필 저장
- `POST /users` — 사용자 기본 정보(email, name, school, major, grade, enrollment_status, interest_companies, interest_jobs)를 받아 DB에 저장한다.
- `PUT /users/{user_id}` — 프로필 부분 업데이트를 지원한다.
- `GET /users/{user_id}` — 저장된 프로필을 반환한다.

## REQ-2: CV 파싱 및 정제
- `POST /users/{user_id}/cv` — CV를 업로드하거나 URL을 제출한다.
  - URL인 경우: httpx로 해당 페이지를 열어 텍스트를 추출한다.
  - PDF 파일인 경우: pypdf로 텍스트를 추출한다.
- 추출된 원문 텍스트를 Pydantic AI Agent(Gemini)에게 전달하여 핵심 정보(기술스택, 경력, 학력, 프로젝트)를 정제한다.
- 정제된 요약을 `users.cv_summary`(TEXT)에 저장한다. (스키마 변경 필요)
- 원본 파일명 또는 URL을 `resume_filename` / `resume_url`에 저장한다.

## REQ-3: 코사인 유사도 기반 공고 필터링
- `GET /users/{user_id}/matching-jobs` — 사용자의 `interest_companies`, `interest_jobs`, `cv_summary`를 기반으로 `job_postings`에서 관련 공고를 필터링한다.
- 사용자 선호도 텍스트와 공고 텍스트(title + company + key_info)를 Gemini embedding으로 벡터화한다.
- 코사인 유사도 상위 N개(기본 10개)를 반환한다.

## REQ-4: LLM 기반 추천 생성
- `POST /users/{user_id}/recommendations` — REQ-3 필터링 결과를 바탕으로 Pydantic AI Agent가 각 공고에 대한 추천 이유와 준비 할 일 목록을 생성한다.
- 결과를 `ai_recommendations` 테이블에 저장한다 (post_id 대신 job_posting_id 참조).
- `GET /users/{user_id}/recommendations` — 저장된 추천 목록을 반환한다.

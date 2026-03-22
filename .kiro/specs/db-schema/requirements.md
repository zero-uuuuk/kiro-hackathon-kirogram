# Requirements: DB Schema 확장

## REQ-1: 사용자 정보 확장
- `users` 테이블에 이력서(PDF 파일명 또는 URL), 관심회사 목록, 관심직무 목록 컬럼을 추가한다.
- 이력서는 PDF 업로드(파일명)와 외부 URL 두 가지 방식을 모두 지원한다.

## REQ-2: 직무 공고 테이블
- 채용공고 제목, 기업, 시작일, 마감일, 핵심정보(직무요건), 원본 파일명을 저장하는 `job_postings` 테이블을 생성한다.
- 각 공고는 Pinecone 벡터 ID(`pinecone_id`)를 저장하여 벡터 DB와 참조 관계를 유지한다.
- 공고 저장 시 Pinecone에 동시 upsert한다 (애플리케이션 레이어 책임, 스키마는 ID만 보관).

## REQ-3: AI Agent 응답 기록
- Agent 대화 세션 단위로 메시지 이력을 저장하는 `agent_sessions` 테이블을 생성한다.
- 어떤 종류의 Agent인지(`agent_type`)를 구분할 수 있어야 한다.
- 메시지는 `[{role, content, timestamp}]` 형태의 JSONB 배열로 저장한다.

## REQ-4: 학사정보 수집 및 저장
- 사용자 기준으로 키워드 필터링된 학사정보를 저장하는 `academic_notices` 테이블을 생성한다.
- 벡터 DB는 사용하지 않는다. 키워드 배열(`keywords`)로 매칭 근거를 보존한다.
- 동일 사용자 + 동일 URL의 중복 저장을 방지한다.

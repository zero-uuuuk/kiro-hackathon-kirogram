# Requirements: CJ 채용공고 스크래퍼

## REQ-1: 공고 리스트 수집
- 주어진 리스트 URL(https://recruit.cj.net/recruit/ko/recruit/recruit/list.fo)에서 모든 공고 상세 URL을 수집한다.
- 각 공고는 `zz_jo_num` 파라미터로 식별된다.

## REQ-2: 공고 JPG 다운로드
- 각 공고 상세 페이지(detail.fo?zz_jo_num=...)에서 직무 공고 JPG 이미지를 다운로드한다.
- 다운로드된 파일은 `backend/downloads/` 디렉토리에 저장한다.
- 파일명은 `{zz_jo_num}.jpg` 형식을 따른다.

## REQ-3: AI Agent 기반 실행
- Pydantic AI Framework를 사용한 Agent가 스크래핑 도구를 호출하여 작업을 수행한다.
- Gemini API(`GEMINI_API_KEY` from `.env`)를 LLM으로 사용한다.
- Agent는 (1) 리스트 수집 툴, (2) JPG 다운로드 툴 두 가지 도구를 가진다.

## REQ-4: 환경 설정
- `.env`에서 `GEMINI_API_KEY`를 로드한다.
- `playwright`로 브라우저 자동화를 수행한다.

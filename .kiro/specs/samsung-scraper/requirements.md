# Requirements: 삼성 채용공고 스크래퍼

## REQ-1: 공고 리스트 수집
- https://www.samsungcareers.com/hr/ 의 `/hr/list.data` API 응답에서 공고 ID(`seqno`) 목록을 수집한다.
- 각 공고는 `data-value` 속성(쉼표 포함 숫자, 예: `"22,032"`)으로 식별된다.

## REQ-2: 공고 상세 텍스트 스크랩
- 각 공고의 `/recruit/detail.data?seqno={seqno}` API를 호출하여 JSON 응답을 수집한다.
- 수집 대상 필드: `title`, `cmpNameKr`, `startdate`, `enddate`, `introKr`, `stepKr`, `processKr`, `attachmentKr`

## REQ-3: AI Agent 노이즈 제거
- Pydantic AI Agent가 수집된 원본 텍스트에서 불필요한 노이즈(HTML 태그, 중복 공백, 특수문자, 무관한 안내문구 등)를 제거하고 핵심 정보만 정제하여 반환한다.
- Gemini API(`GEMINI_API_KEY` from `.env`)를 LLM으로 사용한다.

## REQ-4: 결과 저장
- 정제된 공고 데이터를 `backend/samsung_jobs/` 디렉토리에 `{seqno}.json` 파일로 저장한다.

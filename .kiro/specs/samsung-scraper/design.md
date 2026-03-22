# Design: 삼성 채용공고 스크래퍼

## 아키텍처

```
backend/samsung_scraper.py   ← 진입점 (Agent 실행)
backend/samsung_jobs/        ← JSON 저장 디렉토리
```

## Agent 설계

- Model: `google-gla:gemini-2.0-flash` (pydantic-ai)
- Tools:
  - `collect_seqno_list() -> list[str]`: 리스트 페이지에서 seqno 목록 반환
  - `scrape_job_detail(seqno: str) -> str`: detail.data API 호출 → Agent가 노이즈 제거 → JSON 저장 → 저장 경로 반환

## 스크래핑 전략

- `collect_seqno_list`: playwright로 `/hr/` 로드 → `/hr/list.data` 응답 인터셉트 → HTML에서 `data-value` 속성 파싱 → 쉼표 제거하여 seqno 반환
- `scrape_job_detail`: httpx로 `/recruit/detail.data?seqno={seqno}` 직접 호출 → `data.result` 에서 대상 필드 추출 → 원본 텍스트를 Agent에게 전달하여 노이즈 제거 요청

## 노이즈 제거 대상

- HTML 태그 (`<br>`, `<p>` 등)
- 중복 공백 및 불필요한 줄바꿈
- 홈페이지 URL, 로그인 안내 등 무관한 안내문구
- 특수문자 남용

## 저장 형식

```json
{
  "seqno": "22032",
  "title": "...",
  "company": "...",
  "startdate": "...",
  "enddate": "...",
  "intro": "...",
  "step": "...",
  "process": "...",
  "attachment": "..."
}
```

## 불변 제약

- `/hr/list.data` 응답은 HTML 형식이므로 BeautifulSoup 없이 정규식 또는 playwright DOM으로 파싱한다.
- `detail.data` API는 로그인 없이 호출 가능하므로 httpx 직접 호출을 사용한다.

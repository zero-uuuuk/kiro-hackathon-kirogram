# Design: CJ 채용공고 스크래퍼

## 아키텍처

```
backend/job_scraper.py   ← 진입점 (Agent 실행)
backend/downloads/       ← JPG 저장 디렉토리
```

## Agent 설계

- Model: `google-gla:gemini-2.0-flash` (pydantic-ai)
- Tools:
  - `collect_job_list() -> list[str]`: 리스트 페이지에서 zz_jo_num 목록 반환
  - `download_job_jpg(zz_jo_num: str) -> str`: 상세 페이지에서 JPG 다운로드 후 저장 경로 반환

## 스크래핑 전략

- `collect_job_list`: playwright로 리스트 페이지 로드 → `a[href*="detail.fo"]` 셀렉터로 링크 수집 → URL에서 `zz_jo_num` 파라미터 추출
- `download_job_jpg`: playwright로 상세 페이지 로드 → `img[src*=".jpg"]` 또는 네트워크 응답 인터셉트로 JPG URL 획득 → httpx로 다운로드

## 파일 저장

- 저장 경로: `backend/downloads/{zz_jo_num}.jpg`
- 디렉토리 없으면 자동 생성

## 의존성 추가 (requirements.txt)

- `pydantic-ai[google]`
- `playwright` (이미 존재)

# Kirogram

공고 크롤러 + AI 추천 플랫폼.

## Two-Agent Crawler (AnalyzerAgent + ExecutorAgent)

임의의 URL을 입력하면 AI가 사이트 구조를 분석하고 자동으로 크롤링합니다.

```bash
# Agent 1만 실행: 사이트 분석 → CrawlStrategy JSON 출력
python -m crawler.analyze https://devpost.com/hackathons --category hackathon

# Agent 1 + Agent 2: 분석 후 바로 크롤링 → DB 저장
python -m crawler.analyze https://devpost.com/hackathons --category hackathon --execute
```

**Agent 1 (AnalyzerAgent)**: URL의 HTML 구조를 Bedrock Claude로 분석해 제목·회사·마감일·설명 필드의 CSS 셀렉터와 페이지네이션 패턴을 추출합니다.

**Agent 2 (ExecutorAgent)**: Agent 1의 전략을 받아 Playwright로 실제 크롤링을 수행하고 PostgreSQL에 저장합니다.

## Crawler Agent

AWS Bedrock Claude(Haiku)로 JS 렌더링 페이지를 분석해 구조화된 공고 데이터를 PostgreSQL에 저장하는 에이전트.

- 페이지 내 이미지(최대 5개)는 Bedrock Claude vision으로 OCR 처리
- 첨부파일(.pdf/.docx/.hwp/.pptx, 최대 3개)은 다운로드 후 텍스트 추출
- 이미지/첨부파일 추출 실패 시 graceful degradation (크롤링 계속 진행)

### 지원 사이트

| 사이트 | 카테고리 |
|---|---|
| linkareer.com | job |
| wanted.co.kr | job |
| saramin.co.kr | job |
| devpost.com | hackathon |
| dacon.io | competition |

### 환경변수 설정

`backend/.env`:

```
DATABASE_URL=postgresql://...
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=us-east-1
```

### 설치

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### DB 초기화

```bash
python -m crawler.init_db
```

### 실행

```bash
# 전체 사이트 크롤링
python -m crawler

# 특정 사이트만
python -m crawler --site devpost

# 페이지 수 제한
python -m crawler --site saramin --max-pages 2
```

## Recommender Agent

크롤링된 공고를 사용자 프로필(학교/전공/학년/관심분야)과 매칭해 맞춤 추천을 생성.

- AWS Bedrock Claude Haiku로 relevance_score 산출 (0.0~1.0)
- 0.5 이상인 공고만 `ai_recommendations` 테이블에 저장
- 추천 이유(한국어) + 할 일 목록(todos) 함께 저장

## Scheduler

매일 지정 시간에 크롤링 → 추천 자동 실행.

```bash
# 실행 (기본 09:00 KST)
python backend/scheduler.py

# 시간 변경
CRAWL_SCHEDULE_HOUR=7 python backend/scheduler.py
```

환경변수: `CRAWL_SCHEDULE_HOUR` (기본값: 9)

## Notification API

사용자 접속 시 미확인 맞춤 공고 조회.

```bash
# 서버 실행
cd backend
uvicorn api.main:app --reload
```

### 엔드포인트

```
GET  /notifications?user_id=1
     → 미확인 추천 공고 목록 (relevance_score 내림차순)

POST /notifications/read
     Body: {"user_id": 1, "post_ids": [2, 3]}
     → 읽음 처리
```

## Architecture

```
Scheduler (APScheduler, 09:00 KST)
  → CrawlerOrchestrator
    → SiteStrategy (5 sites)
    → PageFetcher (Playwright)
    → BedrockExtractor (Claude Haiku)
    → posts 테이블 저장
  → RecommenderAgent
    → users × posts 매칭
    → Bedrock Claude (relevance_score)
    → ai_recommendations 테이블 저장

Notification API (FastAPI)
  GET  /notifications   → 미확인 추천 반환
  POST /notifications/read → 읽음 처리
```

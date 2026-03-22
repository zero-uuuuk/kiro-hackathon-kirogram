---
inclusion: manual
---

# Backend Developer

## Role

백엔드 API 서버와 비즈니스 로직을 담당한다. RESTful API 설계, 데이터베이스 연동, 외부 서비스(Gemini, Pinecone) 통합을 책임진다.

## Tech Stack

- Python 3.11+ with FastAPI
- SQLAlchemy (ORM)
- Pydantic (데이터 검증)
- PostgreSQL (Amazon RDS/Aurora)
- Google Gemini API (AI 기능)
- Pinecone (벡터 DB)
- AWS SDK (boto3)

## Coding Rules

- API 엔드포인트는 RESTful 규칙을 따른다
- 요청/응답 모델은 Pydantic으로 정의한다
- 비즈니스 로직은 라우터에서 분리하여 서비스 레이어에 둔다
- DB 접근은 리포지토리 패턴으로 분리한다
- 환경 변수는 `.env`에서 관리하고 `pydantic-settings`로 로드한다
- 모든 API에 적절한 HTTP 상태 코드와 에러 응답을 반환한다
- 비밀 키는 절대 코드에 하드코딩하지 않는다 (AWS Secrets Manager 사용)
- 비동기(async/await)를 적극 활용한다

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   └── routes/        # API 라우터
│   ├── core/
│   │   ├── config.py      # 설정 관리
│   │   └── security.py    # 인증/인가
│   ├── models/            # SQLAlchemy 모델
│   ├── schemas/           # Pydantic 스키마
│   ├── services/          # 비즈니스 로직
│   ├── repositories/      # DB 접근 레이어
│   ├── utils/             # 유틸리티
│   └── main.py            # FastAPI 앱 진입점
├── tests/
├── alembic/               # DB 마이그레이션
├── .env
├── .env.example
├── requirements.txt
└── Dockerfile
```

## API Design

- 엔드포인트 네이밍: `/api/v1/{resource}`
- 페이지네이션: `?page=1&size=20`
- 에러 응답 형식: `{"detail": "message", "code": "ERROR_CODE"}`
- CORS 설정을 프론트엔드 도메인에 맞게 구성한다
- API 문서는 FastAPI 자동 생성 Swagger를 활용한다

## External Services

- Gemini API: AI 기반 기능 구현 시 사용, 서비스 레이어에서 호출
- Pinecone: 벡터 검색/임베딩 저장, 전용 서비스 클래스로 래핑
- AWS 서비스: S3(파일), SES(이메일), SQS(큐) 등 boto3로 접근

## Database

- Amazon RDS (PostgreSQL) 사용
- 마이그레이션은 Alembic으로 관리한다
- 커넥션 풀링을 적절히 설정한다
- 쿼리 성능을 고려하여 인덱스를 설계한다

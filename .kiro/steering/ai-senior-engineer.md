---
inclusion: manual
---

# AI Senior Engineer

## Role

AI/ML 파이프라인 설계와 구현을 총괄한다. Gemini API 활용, 벡터 검색(Pinecone), 프롬프트 엔지니어링, RAG 파이프라인 구축을 책임진다.

## Tech Stack

- Google Gemini API (LLM)
- Pinecone (벡터 데이터베이스)
- LangChain 또는 직접 구현 (오케스트레이션)
- Python 3.11+
- NumPy / pandas (데이터 처리)

## Coding Rules

- LLM 호출은 반드시 재시도 로직과 타임아웃을 포함한다
- 프롬프트는 별도 파일 또는 상수로 관리하고 코드에 인라인하지 않는다
- 토큰 사용량을 추적하고 로깅한다
- 벡터 임베딩 차원과 메트릭은 일관되게 유지한다
- AI 응답은 반드시 검증/파싱 후 사용한다 (hallucination 방어)
- 비용 최적화를 항상 고려한다 (캐싱, 배치 처리)
- API 키는 환경 변수로만 관리한다

## AI Architecture

```
┌─────────────┐     ┌──────────────┐     ┌───────────┐
│   사용자     │────▶│  백엔드 API   │────▶│  Gemini   │
│   요청       │     │  (FastAPI)   │     │  API      │
└─────────────┘     └──────┬───────┘     └───────────┘
                           │
                    ┌──────▼───────┐
                    │  Pinecone    │
                    │  (벡터 검색)  │
                    └──────────────┘
```

## RAG Pipeline

1. 문서 수집 → 청킹 → 임베딩 생성 → Pinecone 저장
2. 쿼리 → 임베딩 변환 → Pinecone 유사도 검색 → 컨텍스트 구성
3. 컨텍스트 + 프롬프트 → Gemini API 호출 → 응답 파싱 → 반환

## Key Modules

```
backend/app/
├── services/
│   ├── ai_service.py        # Gemini API 래퍼
│   ├── embedding_service.py # 임베딩 생성/관리
│   ├── vector_service.py    # Pinecone 연동
│   └── rag_service.py       # RAG 파이프라인 오케스트레이션
├── prompts/                 # 프롬프트 템플릿
│   └── templates.py
└── utils/
    └── token_counter.py     # 토큰 사용량 추적
```

## Prompt Engineering

- 시스템 프롬프트와 유저 프롬프트를 명확히 분리한다
- 프롬프트 버전 관리를 한다
- 출력 형식을 명시적으로 지정한다 (JSON, 구조화된 텍스트 등)
- few-shot 예시를 활용하여 응답 품질을 높인다
- 가드레일을 설정하여 부적절한 응답을 필터링한다

## Performance & Cost

- 반복 쿼리에 대한 응답 캐싱 (ElastiCache)
- 임베딩 배치 처리로 API 호출 최소화
- Pinecone 네임스페이스를 활용한 데이터 분리
- Gemini 모델 선택 시 비용 대비 성능 고려

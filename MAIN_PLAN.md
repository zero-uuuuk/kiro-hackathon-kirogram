- Agent Flow 설계
    
    ```mermaid
    flowchart TD
        A[사용자 최초 접속] --> B[Onboarding / Profile Agent]
        B --> C[학교 / 전공 / 학년 / 관심분야 수집]
        C --> D[Interest Expansion Agent]
        D --> E[유사 사용자 기반 관심 키워드 추천]
        E --> F{사용자 선택 / 수정}
        F --> G[최종 관심사 프로필 저장]
    
        G --> H[Monitoring / Discovery Agent]
        H --> I[기본 소스 / 커스텀 URL / 검색 API 탐색]
        I --> J[신규 공고 / 행사 / 일정 후보 수집]
    
        J --> K[Relevance & Calendarability Agent]
        K --> L{사용자에게 관련 있는가?}
        L -- 아니오 --> H
        L -- 예 --> M{일정화 가능한 정보인가?}
        M -- 불확실 --> N[검토 대기 / 사용자 확인 요청]
        M -- 예 --> O[Schedule Structuring Agent]
    
        O --> P[이벤트 초안 생성<br/>제목 / 날짜 / 링크 / 요약]
        P --> Q[Reminder Strategy Agent]
        Q --> R[준비 기간 / 리마인드 시점 추천]
    
        R --> S[사용자에게 카드 형태로 제안]
        S --> T{캘린더에 추가할까?}
        T -- 아니오 --> U[보관 / 넘기기]
        T -- 예 --> V[Calendar Action Agent]
        V --> W[Google Calendar 등록]
        W --> X[리마인드 설정 완료]
        X --> Y[동적 맞춤 캘린더 반영]
    
        Y --> H
       
    ```
    

### 최종 SchedAI 기획서

---

### 한 줄 정의

> 관심사를 등록하면 Agent가 채용공고/해커톤을 자동 수집해 카드뉴스로 추천하고, 선택 시 Google Calendar에 자동 등록해주는 데스크탑 앱
> 

---

### 무엇을 만드나

**온보딩 화면**

- 관심사 키워드 입력 (예: "AI/ML, 백엔드, 대학생")
- 학교 선택 (취업포털 크롤링 대상)
- Google Calendar OAuth 연동

**설정 화면**

```
[기본 소스 탭]            [커스텀 소스 탭]
링커리어 ✅               + URL 추가
원티드 ✅                 ─────────────────────
사람인 ✅                 🔗 rocketpunch.com
Devpost ✅                  "스타트업 마케팅 인턴"
한양대 취업포털 ✅         🔗 notion.so/events
                            "AI 관련 행사/밋업"
```

**메인 화면 — 카드뉴스 피드**

- Agent가 수집한 공고를 카드 형태로 표시
- 각 카드: 공고명 / 마감일 / 관련도 점수 / 출처 (기본/커스텀 구분)
- "캘린더 추가" / "넘기기" 선택
- "지금 바로 검색" 버튼 → 온디맨드 Agent 실행

**캘린더 화면**

- 등록된 일정 월간 뷰 (노션 캘린더 스타일)
- 각 일정 클릭 시 공고 상세 내용 확인

---

### Agent 구조

```
[온디맨드 or 스케줄 트리거 (EventBridge)]
        ↓
[Crawler Agent]
├── 기본 소스
│   링커리어 / 원티드 / 사람인 /
│   Devpost / 각 대학 취업포털
│   → Tavily API 웹 서칭
└── 커스텀 소스
    ├── DynamoDB에서 사용자 등록 URL 로드
    ├── URL 접근 + 페이지 내용 파싱
    └── "원하는 정보 설명" 기반으로
        Agent가 추출 항목 스스로 판단
        → 제목 / 마감일 / 링크 / 핵심 내용 추출
        ↓
[Filter Agent]
사용자 프로파일과 공고 매칭
관련도 점수 산출 (Bedrock Claude)
상위 N개 추천 선별
        ↓
[Card Generator Agent]
공고 내용 → 카드뉴스 형태 요약
마감일 / 지원기간 / 핵심 자격요건 추출
        ↓
[사용자 선택: 캘린더 추가?]
        ↓ YES
[Calendar Agent]
공고 내용 분석 → 날짜 정보 추출
(지원 시작일 / 마감일 / 발표일)
Google Calendar API로 일정 자동 등록
```

---

### 기술 스택 (AWS 기반)

| 파트 | 스택 |
| --- | --- |
| 데스크탑 앱 | Electron + React + Tailwind |
| 백엔드 | AWS Lambda + API Gateway |
| LLM + Agent | Amazon Bedrock (Claude) |
| 웹 서칭 | Tavily API |
| 스케줄러 | AWS EventBridge |
| 데이터 저장 | DynamoDB |
| 캘린더 연동 | Google Calendar API |
| 개발 도구 | AWS Kiro |

---

### DynamoDB 스키마

```
UserProfile 테이블
- user_id
- keywords           관심사 키워드 목록
- school             학교 (취업포털 크롤링 대상)
- created_at

CustomSource 테이블
- user_id
- url                사용자 등록 URL
- description        원하는 정보 설명
- last_crawled_at    마지막 크롤링 시각
- is_active          활성/비활성 토글

Post 테이블
- post_id
- user_id
- title              공고명
- source             출처 (기본/커스텀 구분)
- deadline           마감일
- relevance_score    관련도 점수
- raw_content        원문 내용
- is_added           캘린더 추가 여부
- created_at
```

---

### Kiro 3요소 활용

**Spec** — 10:00~11:30

- Kiro에게 자연어로 아이디어 설명
- Kiro가 요구사항 / API명세 / DynamoDB 스키마 자동 생성
- 팀이 검토 후 수정/승인 → 스크린샷 저장 (점수 증거)

**Subagent** — 14:00~18:00

- Lambda 5개 + DynamoDB + EventBridge 인프라 생성을 Kiro에게 위임
- 커스텀 URL 분석 + Calendar Agent 날짜 추출 자율 실행

**Hooks** — 18:00~19:00

```
코드 저장
    ↓ 자동 트리거
Lambda 함수 단위 테스트
    ↓ 통과
API Gateway + Lambda 자동 배포
    ↓ 실패 시
배포 중단 + 에러 알림
```

---

### 평가기준 커버 맵

| 평가항목 | 점수 | 커버하는 것 |
| --- | --- | --- |
| Prompt/Spec Quality | 25점 | Kiro Spec 생성 + 팀 수정/승인 과정 |
| Agentic Thinking | 25점 | Crawler → Filter → Card → Calendar 자율 4단계 + 커스텀 URL 스스로 분석 |
| Campus Impact | 15점 | 취업/해커톤 정보 파편화 문제 + 커스텀 소스로 확장성 |
| Completeness | 15점 | Hooks 자동 배포 + 실제 구동 데스크탑 앱 |

---

### 역할 분담

| 시간 | 프론트 (Electron/React) | 백엔드/인프라 | AI |
| --- | --- | --- | --- |
| 10~12시 | Spec 검토 + UI 와이어프레임 | Lambda 구조 + DynamoDB 설계 | Bedrock Agent 설정 |
| 13~15시 | 카드뉴스 피드 + 설정 화면 | Crawler + Filter Lambda | Tavily 연동 + 커스텀 URL 분석 로직 |
| 15~18시 | 캘린더 화면 UI | Calendar Agent Lambda | 날짜 추출 + 관련도 점수 프롬프트 튜닝 |
| 18~19시 | 최종 UI 점검 | Kiro Hooks 설정 + 배포 | 추천 정확도 테스트 |
| 19~21시 | 데모 리허설 |  |  |

### 온보딩 화면 구성

학교랑 전공, 학년 선택

최근 관심 분야 → 객관식으로 옵션을 준다.

(옵션) 개인화 url → 얘는 주소는 url로 받고 관심사는 자연어로 받고
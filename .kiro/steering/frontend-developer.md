---
inclusion: manual
---

# Frontend Developer

## Role

프론트엔드 UI/UX 구현을 담당한다. React 기반 SPA를 개발하며, 백엔드 API와의 통신, 상태 관리, 반응형 디자인을 책임진다.

## Tech Stack

- React 18+ with TypeScript
- Vite (빌드 도구)
- Tailwind CSS (스타일링)
- React Router (라우팅)
- Axios 또는 fetch (API 통신)
- Zustand 또는 React Context (상태 관리)

## Coding Rules

- 컴포넌트는 함수형으로만 작성한다
- Props에는 반드시 TypeScript 인터페이스를 정의한다
- 재사용 가능한 컴포넌트는 `components/` 하위에 분리한다
- 페이지 단위 컴포넌트는 `pages/` 하위에 둔다
- API 호출 로직은 `services/` 또는 `api/` 디렉토리에 분리한다
- 환경 변수는 `.env`에서 관리하고 코드에 하드코딩하지 않는다
- 에러 바운더리를 적용하여 UI 크래시를 방지한다
- 접근성(a11y)을 고려한 시맨틱 HTML을 사용한다

## Project Structure

```
frontend/
├── src/
│   ├── components/    # 재사용 가능한 UI 컴포넌트
│   ├── pages/         # 페이지 단위 컴포넌트
│   ├── hooks/         # 커스텀 훅
│   ├── services/      # API 통신 로직
│   ├── types/         # TypeScript 타입 정의
│   ├── utils/         # 유틸리티 함수
│   ├── styles/        # 글로벌 스타일
│   ├── App.tsx
│   └── main.tsx
├── public/
├── .env.example
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

## API Communication

- 백엔드 API base URL은 환경 변수 `VITE_API_URL`로 관리한다
- API 응답 타입은 `types/`에 정의하고 서비스 레이어에서 사용한다
- 로딩, 에러, 성공 상태를 명시적으로 처리한다
- 인증 토큰은 요청 인터셉터에서 자동 첨부한다

## Deployment

- 빌드 결과물은 Amazon S3 + CloudFront로 배포한다
- 환경별 설정은 `.env.production`, `.env.development`로 분리한다

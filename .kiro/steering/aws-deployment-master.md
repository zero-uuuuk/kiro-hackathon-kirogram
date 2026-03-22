---
inclusion: manual
---

# AWS Deployment Master

## Role

AWS 인프라 설계, 프로비저닝, 배포 파이프라인 구축을 총괄한다. IaC(Infrastructure as Code)로 모든 리소스를 관리하고, CI/CD 파이프라인을 구성한다.

## Tech Stack

- AWS CDK 또는 CloudFormation (IaC)
- AWS CodePipeline / CodeBuild (CI/CD)
- Docker (컨테이너화)
- Amazon ECS Fargate (백엔드 호스팅)
- Amazon S3 + CloudFront (프론트엔드 호스팅)
- Amazon RDS Aurora PostgreSQL (데이터베이스)
- Amazon ElastiCache Redis (캐싱)
- AWS Secrets Manager (시크릿 관리)
- Amazon CloudWatch (모니터링/로깅)
- Amazon Route 53 (DNS)
- AWS Certificate Manager (SSL/TLS)

## Infrastructure Rules

- 모든 인프라는 IaC로 관리한다. 콘솔 수동 작업 금지
- 환경별(dev, staging, prod) 분리를 철저히 한다
- 최소 권한 원칙(Least Privilege)을 적용한다
- 퍼블릭 서브넷에는 최소한의 리소스만 배치한다
- 시크릿은 AWS Secrets Manager로 관리한다
- 태깅 정책을 일관되게 적용한다
- 비용 알림을 설정한다

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  CloudFront                      │
│              (프론트엔드 CDN)                     │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│                 S3 Bucket                        │
│            (React 빌드 결과물)                    │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│              API Gateway                         │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│              ECS Fargate                         │
│           (FastAPI 백엔드)                        │
│         ┌──────────────────┐                     │
│         │  Task Definition │                     │
│         │  - app container │                     │
│         └──────────────────┘                     │
└────────────────────┬────────────────────────────┘
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
    ┌──────────┐ ┌────────┐ ┌──────────┐
    │ RDS      │ │ Elasti │ │ Secrets  │
    │ Aurora   │ │ Cache  │ │ Manager  │
    └──────────┘ └────────┘ └──────────┘
```

## VPC Design

```
VPC (10.0.0.0/16)
├── Public Subnet (10.0.1.0/24, 10.0.2.0/24)
│   ├── NAT Gateway
│   └── ALB
├── Private Subnet (10.0.10.0/24, 10.0.11.0/24)
│   ├── ECS Fargate Tasks
│   └── ElastiCache
└── Isolated Subnet (10.0.20.0/24, 10.0.21.0/24)
    └── RDS Aurora
```

## CI/CD Pipeline

```
GitHub Push
  → CodePipeline 트리거
    → CodeBuild (테스트 + 빌드)
      → ECR (Docker 이미지 푸시)
        → ECS 배포 (Blue/Green 또는 Rolling)
```

- 프론트엔드: S3 sync + CloudFront invalidation
- 백엔드: Docker 빌드 → ECR 푸시 → ECS 서비스 업데이트

## Monitoring & Alerting

- CloudWatch Logs로 애플리케이션 로그 수집
- CloudWatch Alarms로 CPU, 메모리, 에러율 모니터링
- SNS 토픽으로 알림 전송
- X-Ray로 분산 추적 (선택)

## Security

- WAF를 CloudFront/API Gateway에 적용
- Security Group은 필요한 포트만 개방
- RDS는 Isolated Subnet에 배치, 퍼블릭 접근 차단
- SSL/TLS 인증서는 ACM으로 관리
- IAM Role 기반 접근 제어 (Access Key 사용 최소화)

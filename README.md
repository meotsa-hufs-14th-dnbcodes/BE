# Chrono-Derm

시술 후 피부 상태와 생활 습관을 추적해 "보존지수"로 보여주고, 셀카 분석을 기반으로 오늘의 케어를 추천해주는 서비스의 백엔드.

## 서비스 소개

미용 시술의 효과가 시간이 지나며 얼마나 남았는지는 감으로만 판단하게 되고, 관리도 시술 직후에만 반짝 신경 쓰다 흐지부지되기 쉽다. 시술 기록과 얼굴 상태를 이어서 관리할 도구가 없어 "지금 얼마나 남았지", "오늘은 뭘 하면 좋지" 같은 질문에 답하기 어렵다.

이 서비스는 시술 기록 · 데일리 체크 · 셀카 분석을 모아 보존지수로 계산하고, 그 값을 기반으로 오늘의 케어 추천과 재시술 알림까지 한 번에 이어지도록 만든다.

## 핵심 플로우

- 시술/데일리체크 기록: 시술 이력과 자외선차단제·재생크림·흡연·음주·운동 여부를 등록
- 셀카 업로드: `selfie` 앱이 받아 별도 `selfie_analysis` 서비스로 전달, 즉시 202 응답
- AI 피부 분석: `selfie_analysis`가 PerfectCorp에 분석을 맡기고, 완료 시 webhook으로 결과 수신
- 보존지수 계산: 오늘 실측치와 기대 감쇠치를 비교해 지수를 산출하고 데일리 체크인으로 보정.
- 케어 추천/알림: Rule Engine + OpenAI로 오늘의 케어를 생성, 재시술 임박 시 알림 발송

## 아키텍처 구성 요소

| 구성 요소                       | 역할                                                                |
| ------------------------------- | ------------------------------------------------------------------- |
| Django + DRF :8000 (Docker)     | 회원/시술기록/데일리 체크인/보존지수/케어추천/알림 API, Bearer 인증 |
| selfie_analysis (Django, :8001) | 셀카 이미지 벤더(PerfectCorp) 연동 전담 마이크로서비스              |
| MySQL                           | 각 서비스 도메인 데이터 영속화                                      |
| PerfectCorp API                 | 피부 CV 분석 수행, 완료 시 webhook 콜백                             |
| Redis + Celery (worker/beat)    | 재시술 알림, 주간 보존지수 리포트 등 정기 알림 스케줄링             |
| OpenAI API                      | 오늘의 케어 추천 자연어 요약 생성                                   |
| Nginx + Certbot                 | TLS 종단, 리버스 프록시, Let's Encrypt 인증서 자동 갱신             |
| GitHub Actions                  | PR 검증(CI) + main push 시 SSH 기반 EC2 배포(CD)                    |

## 설계 포인트

**셀카 분석은 별도 마이크로서비스로 분리한다.** PerfectCorp 연동, 업로드/폴링/재시도, webhook 서명 검증 책임을 메인 서비스에서 떼어내 `selfie_analysis`가 전담하고, provider 추상화(`providers/`)로 벤더 교체에 대비한다.

**분석 요청은 동기 202 응답 + webhook 체이닝으로 처리한다.** 셀카 업로드 요청 안에서는 벤더 업로드와 분석 시작까지만 동기로 처리해 바로 202를 반환하고, 실제 완료는 PerfectCorp webhook → 내부 webhook으로 이어받아 알림을 생성한다. 분석에 수십 초~분이 걸려도 요청 스레드가 묶이지 않는다.

**내부 호출과 외부 벤더 webhook의 인증 경계를 분리한다.** 서비스 간 호출은 `X-Service-Token` 고정 토큰으로, PerfectCorp webhook은 Standard Webhooks HMAC-SHA256 서명으로 검증해 서로 다른 신뢰 경계를 명확히 나눈다.

**보존지수는 기대 감쇠치 대비 실측치로 계산한다.** 시술 카테고리별로 참고할 CV 지표를 매핑하고, 시술 지속기간 기반 기대 감쇠치(E(D))와 오늘 실측치(A(D))를 비교해 기본 지수를 구한 뒤, 데일리 체크인 보정치로 생활 습관을 반영한다.

**케어 추천은 Rule Engine → LLM 순으로 폴백을 둔다.**
데일리 체크인·시술이력·보존지수로 규칙 기반 Action을 먼저 고르고 OpenAI로 자연어 요약을 입히되, LLM이 실패하면 카탈로그 원문으로, 추천할 Action이 없으면 기본 루틴으로 대체한다.

**보존지수 산출은 셀카 분석과 데일리 체크인 중 나중에 끝나는 쪽이 트리거한다.** 사용자가 셀카를 먼저 찍든 데일리 체크인를 먼저 작성하든 순서에 상관없이, 두 조건이 모두 갖춰지는 시점에 자동으로 계산되도록 대기 상태(`PendingPreservationCalc`)를 둔다.

## 패키지 구조

```
BE/
├── chronoProject/       # 프로젝트 설정 + 배포 자산(docker-compose, nginx, cert)
├── accounts/            # 회원가입, 로그인, Bearer 인증
├── proc/                # 시술 카테고리 / 시술 / 시술 기록
├── checklist/           # 데일리 체크인
├── selfie/              # selfie_analysis 연동 클라이언트 & 내부 webhook 수신
├── preservation/        # 보존지수 계산
├── care/                # 오늘의 케어 추천 (Rule Engine + OpenAI)
├── notifications/       # 알림 생성/조회, Celery 태스크
├── selfie_analysis/     # 별도 Django 프로젝트: 셀카 분석 벤더 연동
│   └── analysis/        #   모델, 뷰, 태스크, PerfectCorp provider
└── manage.py
```

## 기술 스택

| 구분               | 내용                                                             |
| ------------------ | ---------------------------------------------------------------- |
| Language / Runtime | Python 3.13                                                      |
| Framework          | Django 6.1, Django REST Framework                                |
| DB                 | MySQL 8.4                                                        |
| 비동기/스케줄링    | Celery, Redis, django_celery_results                             |
| 외부 연동          | PerfectCorp API, standardwebhooks, OpenAI API                    |
| API 문서           | drf-yasg (Swagger/ReDoc)                                         |
| 인프라             | AWS EC2 (단일 인스턴스)                                          |
| 배포               | Docker, Docker Compose, Gunicorn, Nginx, Certbot, GitHub Actions |

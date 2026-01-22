# FinanceAI 아키텍처

## 시스템 개요

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                        │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐            │
│  │ 대시보드 │  │종목상세 │  │  채팅   │  │ 리서치  │            │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘            │
└───────┼────────────┼────────────┼────────────┼──────────────────┘
        │            │            │            │
        ▼            ▼            ▼            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend API (FastAPI)                       │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐            │
│  │ /stock  │  │/analysis│  │  /chat  │  │/research│            │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘            │
└───────┼────────────┼────────────┼────────────┼──────────────────┘
        │            │            │            │
        ▼            ▼            ▼            ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Agent Layer                               │
│  ┌──────────┐  ┌────────────┐  ┌────────┐  ┌──────────┐        │
│  │Technical │  │Fundamental │  │  Chat  │  │ Research │        │
│  │  Agent   │  │   Agent    │  │ Agent  │  │  Agent   │        │
│  └────┬─────┘  └─────┬──────┘  └───┬────┘  └────┬─────┘        │
│       │              │             │            │                │
│       └──────────────┴─────────────┴────────────┘                │
│                          │                                       │
│                    ┌─────┴─────┐                                │
│                    │ BaseAgent │                                │
│                    │  (LLM)    │                                │
│                    └───────────┘                                │
└─────────────────────────────────────────────────────────────────┘
        │            │            │            │
        ▼            ▼            ▼            ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Tools Layer                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │stock_data│  │financials│  │indicators│  │news_search│        │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘        │
└───────┼─────────────┼─────────────┼─────────────┼───────────────┘
        │             │             │             │
        ▼             ▼             ▼             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     External Data Sources                        │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐            │
│  │yfinance │  │  pykrx  │  │OpenDART │  │News API │            │
│  │  (US)   │  │  (KR)   │  │  (KR)   │  │         │            │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

## 디렉토리 구조

```
FinanceAI/
├── src/                          # 백엔드 소스
│   ├── agents/                   # AI 에이전트
│   │   ├── base_agent.py         # 기반 클래스 (LLM 호출)
│   │   ├── technical/            # 기술적 분석
│   │   │   ├── __init__.py
│   │   │   └── agent.py
│   │   ├── fundamental/          # 기본적 분석
│   │   │   ├── __init__.py
│   │   │   └── agent.py
│   │   ├── research/             # 리서치 리포트
│   │   │   ├── __init__.py
│   │   │   └── agent.py
│   │   └── chat/                 # AI 채팅
│   │       ├── __init__.py
│   │       └── agent.py
│   │
│   ├── api/                      # FastAPI 애플리케이션
│   │   ├── main.py               # 앱 엔트리포인트
│   │   └── routers/              # API 라우터
│   │       ├── stock.py          # 주식 데이터 API
│   │       ├── analysis.py       # 분석 API
│   │       ├── research.py       # 리서치 API
│   │       ├── chat.py           # 채팅 API
│   │       └── system.py         # 시스템 API
│   │
│   ├── tools/                    # 데이터 도구
│   │   ├── stock_data.py         # 주가 데이터
│   │   ├── financials.py         # 재무 데이터
│   │   ├── indicators.py         # 기술적 지표
│   │   └── news_search.py        # 뉴스 검색
│   │
│   ├── core/                     # 핵심 유틸리티
│   │   ├── config.py             # 설정 관리
│   │   └── errors.py             # 예외 클래스
│   │
│   ├── services/                 # 서비스 레이어 (확장용)
│   └── utils/                    # 유틸리티
│
├── web/                          # 프론트엔드 소스
│   ├── app/                      # Next.js App Router
│   │   ├── layout.tsx            # 루트 레이아웃
│   │   ├── page.tsx              # 홈페이지
│   │   ├── globals.css           # 글로벌 스타일
│   │   ├── stock/
│   │   │   └── [symbol]/
│   │   │       └── page.tsx      # 종목 상세
│   │   └── chat/
│   │       └── page.tsx          # AI 채팅
│   │
│   ├── components/               # React 컴포넌트
│   │   └── ui/                   # UI 컴포넌트
│   │
│   ├── lib/                      # 유틸리티
│   │   └── api.ts                # API 클라이언트
│   │
│   ├── types/                    # TypeScript 타입
│   │   └── index.ts
│   │
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   └── next.config.js
│
├── config/                       # 설정 파일
│   ├── main.yaml                 # 시스템 설정
│   └── agents.yaml               # 에이전트 설정
│
├── data/                         # 데이터 저장소
│   ├── user/                     # 사용자 데이터
│   │   ├── research/             # 리서치 리포트
│   │   └── analysis/             # 분석 결과
│   └── cache/                    # 캐시
│
├── scripts/                      # 실행 스크립트
│   ├── start_web.py              # 전체 실행
│   └── run_server.py             # 백엔드만 실행
│
├── tests/                        # 테스트
│   ├── agents/
│   ├── tools/
│   └── services/
│
├── docs/                         # 문서
│   ├── PROJECT_STATUS.md         # 프로젝트 현황
│   ├── NEXT_STEPS.md             # 다음 단계
│   └── ARCHITECTURE.md           # 아키텍처 (이 파일)
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pyproject.toml
├── .env.example
├── .gitignore
├── README.md
└── CLAUDE.md
```

## 에이전트 구조

### BaseAgent

모든 에이전트의 기반 클래스. LLM 호출 로직 캡슐화.

```python
class BaseAgent:
    def __init__(self, model, temperature, max_tokens)
    async def call_llm(messages) -> str
    async def stream_llm(messages) -> AsyncIterator[str]
    async def process(*args, **kwargs) -> dict  # 추상 메서드
```

### 에이전트별 역할

| 에이전트 | 역할 | 도구 사용 |
|---------|------|----------|
| TechnicalAgent | 기술적 지표 분석 및 해석 | stock_data, indicators |
| FundamentalAgent | 재무제표 분석 및 밸류에이션 | stock_data, financials |
| ChatAgent | 자연어 질의응답 | Tool Calling (stock_data, news) |
| ResearchAgent | 종합 리서치 리포트 생성 | 모든 도구 |

## 데이터 흐름

### 기술적 분석 요청

```
1. 사용자 요청 (Frontend)
   └─→ POST /api/v1/analysis/technical
       └─→ TechnicalAnalysisAgent.analyze()
           ├─→ stock_data.get_stock_price()
           ├─→ indicators.calculate_indicators()
           └─→ LLM 분석 요약 생성
               └─→ 결과 반환
```

### AI 채팅 요청

```
1. 사용자 질문 (Frontend)
   └─→ POST /api/v1/chat/query
       └─→ ChatAgent.chat()
           └─→ LLM with Tools
               ├─→ [Tool Call] get_stock_price
               ├─→ [Tool Call] get_stock_info
               └─→ [Tool Call] search_news
                   └─→ 최종 응답 생성
```

## 설정 관리

### 환경 변수 우선순위

```
1. 환경 변수 (.env)
2. YAML 설정 (config/*.yaml)
3. 기본값 (코드 내)
```

### 주요 설정 파일

- `.env` - API 키, 포트 등 민감 정보
- `config/main.yaml` - 시스템 설정, 도구 설정
- `config/agents.yaml` - 에이전트별 LLM 파라미터

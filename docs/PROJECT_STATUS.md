# FinanceAI 프로젝트 현황

> 마지막 업데이트: 2026-01-20

## 프로젝트 개요

DeepTutor 아키텍처를 기반으로 한 AI 주식 분석 플랫폼. 한국(KRX) 및 미국(NYSE/NASDAQ) 시장 지원.

**🎯 목표 비전**: Google NotebookLM처럼 다양한 데이터 소스(문서, 웹, 유튜브, 주가)를 조합하여 AI 에이전트로 종목을 분석하고 추천하는 시스템

**상세 비전 문서**: `docs/VISION.md` 참조

## 완료된 작업 (Phase 1)

### 1. 프로젝트 구조 설정 ✅

```
FinanceAI/
├── src/                    # 백엔드 Python 코드
├── web/                    # 프론트엔드 Next.js
├── config/                 # 설정 파일
├── data/                   # 데이터 저장소
├── scripts/                # 실행 스크립트
├── tests/                  # 테스트 코드
└── docs/                   # 문서
```

### 2. 백엔드 구현 ✅

#### 에이전트 모듈 (`src/agents/`)
- [x] `base_agent.py` - 모든 에이전트의 기반 클래스
- [x] `technical/agent.py` - 기술적 분석 에이전트
- [x] `fundamental/agent.py` - 기본적 분석 에이전트
- [x] `research/agent.py` - 리서치 리포트 생성 에이전트
- [x] `chat/agent.py` - AI 질의응답 에이전트 (Tool Calling 지원)

#### 데이터 도구 (`src/tools/`)
- [x] `stock_data.py` - 주가/종목정보 (yfinance, pykrx)
- [x] `financials.py` - 재무제표/재무비율
- [x] `indicators.py` - 기술적 지표 계산 (SMA, EMA, RSI, MACD, 볼린저밴드 등)
- [x] `news_search.py` - 뉴스 검색

#### API 엔드포인트 (`src/api/routers/`)
- [x] `stock.py` - 주가/종목정보 API
- [x] `analysis.py` - 기술적/기본적 분석 API
- [x] `research.py` - 리서치 리포트 API
- [x] `chat.py` - AI 채팅 API (WebSocket 포함)
- [x] `system.py` - 시스템 상태 API

#### 핵심 모듈 (`src/core/`)
- [x] `config.py` - 설정 관리
- [x] `errors.py` - 커스텀 예외 클래스

### 3. 프론트엔드 구현 ✅

#### 페이지 (`web/app/`)
- [x] `page.tsx` - 메인 대시보드 (검색, 기능 카드)
- [x] `stock/[symbol]/page.tsx` - 종목 상세 페이지
- [x] `chat/page.tsx` - AI 채팅 인터페이스

#### 유틸리티
- [x] `lib/api.ts` - API 클라이언트
- [x] `types/index.ts` - TypeScript 타입 정의
- [x] `globals.css` - 글로벌 스타일 (Tailwind)

### 4. 설정 파일 ✅
- [x] `config/main.yaml` - 시스템 설정
- [x] `config/agents.yaml` - 에이전트 LLM 파라미터
- [x] `.env.example` - 환경 변수 템플릿
- [x] `requirements.txt` - Python 의존성
- [x] `package.json` - Node.js 의존성

### 5. DevOps ✅
- [x] `Dockerfile` - 멀티스테이지 Docker 빌드
- [x] `docker-compose.yml` - Docker Compose 설정
- [x] `docker-entrypoint.sh` - Docker 엔트리포인트
- [x] `.gitignore` - Git 제외 파일
- [x] `pyproject.toml` - Python 프로젝트 설정

### 6. 문서 ✅
- [x] `README.md` - 프로젝트 소개
- [x] `CLAUDE.md` - Claude Code 가이드

## 기술 스택

| 영역 | 기술 |
|------|------|
| 백엔드 | FastAPI, Python 3.10+ |
| 프론트엔드 | Next.js 15, React 19, TypeScript |
| 스타일링 | Tailwind CSS |
| LLM | OpenAI API (GPT-4o) |
| 주식 데이터 | yfinance (미국), pykrx (한국) |
| 컨테이너 | Docker, Docker Compose |

## 지원 기능

| 기능 | 상태 | 설명 |
|------|------|------|
| 기술적 분석 | ✅ 구현됨 | SMA, EMA, RSI, MACD, 볼린저밴드, ATR, OBV, VWAP, 스토캐스틱 |
| 기본적 분석 | ✅ 구현됨 | 재무제표, 재무비율, 밸류에이션 |
| AI 질의응답 | ✅ 구현됨 | 자연어 질문, Tool Calling |
| 리서치 리포트 | ✅ 구현됨 | 자동 리포트 생성 |
| 한국 주식 | ✅ 지원 | pykrx 통한 KRX 데이터 |
| 미국 주식 | ✅ 지원 | yfinance 통한 NYSE/NASDAQ |

---

## Phase 1.5: Multi-provider LLM ✅ 완료 (2026-01-19)

### LLM 서비스 (`src/services/llm/`)

Multi-provider LLM 지원 구현 완료:

- [x] `types.py` - LLMConfig, LLMResponse, ToolCall 타입
- [x] `errors.py` - LLMError 계층
- [x] `utils.py` - Provider 자동 감지 (URL/모델 기반)
- [x] `capabilities.py` - Provider/모델별 기능 정의
- [x] `factory.py` - complete(), stream() 통합 인터페이스
- [x] `providers/openai_provider.py` - OpenAI/DeepSeek/Groq
- [x] `providers/anthropic_provider.py` - Anthropic Claude
- [x] `providers/local_provider.py` - Ollama/vLLM/LM Studio

**지원 Provider**:
| Provider | 모델 예시 | 비고 |
|----------|----------|------|
| OpenAI | gpt-4o, gpt-4-turbo | 기본 |
| Anthropic | claude-3-5-sonnet | Tool calling 지원 |
| DeepSeek | deepseek-chat | OpenAI 호환 |
| Groq | llama-3.3-70b | OpenAI 호환 |
| Local | llama3.2 등 | Ollama/vLLM/LM Studio |

**사용 예시**:
```python
# 기존 코드 그대로 동작 (OpenAI)
response = await agent.call_llm(messages)

# Anthropic 사용시 .env 변경만으로 전환
# LLM_BINDING=anthropic
# LLM_MODEL=claude-3-5-sonnet-20241022
```

---

## Phase 2-1: RAG 시스템 ✅ 완료 (2026-01-20)

### 임베딩 서비스 (`src/services/embedding/`)

Multi-provider 임베딩 지원 구현 완료:

- [x] `adapters/base.py` - BaseEmbeddingAdapter, EmbeddingRequest/Response
- [x] `adapters/openai.py` - OpenAI/Azure/DeepSeek/Groq 호환 어댑터
- [x] `adapters/ollama.py` - Ollama 로컬 모델 어댑터
- [x] `provider.py` - EmbeddingProviderManager (어댑터 레지스트리)
- [x] `client.py` - 통합 EmbeddingClient

**지원 Provider**:
| Provider | 모델 예시 | 비고 |
|----------|----------|------|
| OpenAI | text-embedding-3-small/large | 기본 |
| Azure OpenAI | text-embedding-ada-002 | Azure 엔드포인트 |
| Ollama | nomic-embed-text, mxbai-embed-large | 로컬 모델 |
| DeepSeek/Groq | - | OpenAI 호환 |

### RAG 서비스 (`src/services/rag/`)

- [x] `metadata.py` - KB 메타데이터 관리 (metadata.json 영속화)
- [x] `service.py` - RAGService 개선 (KB 자동 발견, 청킹 전략 선택)
- [x] `factory.py` - RAG Pipeline Factory (확장 가능한 구조)
- [x] `components/retrievers/hybrid_retriever.py` - 하이브리드 검색 (Vector + BM25)

**주요 기능**:
- Knowledge Base 생성/삭제/조회
- 문서 업로드 및 자동 인덱싱
- metadata.json 기반 KB 설정 영속화
- Vector 검색 + BM25 키워드 검색 (RRF 결합)
- 시맨틱 청킹 지원

**사용 예시**:
```python
from src.services.rag import get_rag_service

service = get_rag_service()

# KB 생성 및 문서 인덱싱
await service.initialize("my_kb", ["report.pdf", "data.txt"])

# 검색 (LLM 답변 생성 포함)
result = await service.search("매출 현황은?", "my_kb")
print(result.answer)
```

---

## Phase 3: Research Pipeline ✅ 완료 (2026-01-20)

### 데이터 구조 (`src/agents/research/data_structures.py`)

연구 파이프라인을 위한 핵심 데이터 구조 구현:

- [x] `TopicStatus` - 토픽 상태 열거형 (PENDING, RESEARCHING, COMPLETED, FAILED)
- [x] `ToolType` - 도구 유형 열거형 (RAG, WEB, STOCK, FINANCIALS, NEWS, YOUTUBE 등)
- [x] `ToolTrace` - 도구 호출 기록 (인용 ID, 원본 답변, 요약)
- [x] `TopicBlock` - 연구 토픽 블록 (상태 관리, 도구 추적)
- [x] `DynamicTopicQueue` - 동적 토픽 큐 (자동 영속화, 중복 제거)

### 연구 에이전트 (`src/agents/research/agents/`)

6개의 전문화된 에이전트 구현:

| 에이전트 | 역할 | 주요 기능 |
|----------|------|----------|
| `RephraseAgent` | 토픽 최적화 | 사용자 질문을 명확하고 연구 가능한 형태로 변환 |
| `DecomposeAgent` | 토픽 분해 | 큰 주제를 연구 가능한 하위 토픽으로 분할 |
| `ManagerAgent` | 워크플로우 관리 | 진행 상황 평가, 다음 단계 결정, 종료 조건 판단 |
| `ResearchAgent` | 실제 연구 수행 | 도구 호출, 데이터 수집, 인용 기록 |
| `NoteAgent` | 노트 생성 | 연구 결과 요약, 인용 정리, 통찰 추출 |
| `ReportAgent` | 리포트 생성 | 최종 연구 보고서 작성 (Markdown/JSON/HTML) |

### 파이프라인 오케스트레이터 (`src/agents/research/pipeline.py`)

```python
from src.agents.research import ResearchPipeline, run_research

# 파이프라인 생성 및 도구 등록
pipeline = ResearchPipeline()
pipeline.register_tool("stock_data", stock_data_handler)
pipeline.register_tool("financials", financials_handler)

# 연구 실행
result = await pipeline.run(
    topic="삼성전자 2024년 실적 분석 및 투자 전망",
    symbols=["005930"],
    market="KR",
)

# 결과 접근
print(result["report"]["report_content"])
print(result["statistics"])
```

**주요 기능**:
- 6단계 자동 연구 파이프라인 (Rephrase → Decompose → Research → Notes → Synthesis → Report)
- 동적 토픽 추가 (연구 중 발견된 새로운 주제 자동 추가)
- 상태 영속화 (JSON 파일 저장/복원)
- 스트리밍 진행 상황 업데이트 (`run_streaming()`)
- 최대 반복 제한 및 안전 장치

---

## Phase 4: 추가 도구 ✅ 완료 (2026-01-20)

### RAG 도구 (`src/tools/rag_tool.py`)

Knowledge Base 검색 도구:

- [x] `search_knowledge_base()` - KB 검색 및 답변 생성
- [x] `list_knowledge_bases()` - KB 목록 조회
- [x] `execute_rag_tool()` - 에이전트용 도구 실행기
- [x] `RAG_TOOL_DEFINITIONS` - OpenAI Function Calling 정의

### 웹 검색 도구 (`src/tools/web_search.py`)

다중 검색 엔진 지원:

| Provider | 설명 | API 키 |
|----------|------|--------|
| DuckDuckGo | 일반 웹 검색 + 뉴스 | 불필요 |
| Naver | 뉴스/블로그/카페 검색 | 선택적 |
| Google News RSS | 뉴스 RSS 피드 | 불필요 |

- [x] `web_search()` - 통합 검색 인터페이스
- [x] `search_and_store_to_rag()` - 검색 결과 RAG 저장
- [x] `WEB_SEARCH_TOOL_DEFINITIONS` - 에이전트용 도구 정의

### YouTube 도구 (`src/tools/youtube_tool.py`)

유튜브 분석 도구:

- [x] `get_transcript()` - 영상 자막 추출
- [x] `get_channel_videos()` - 채널 최신 영상 목록
- [x] `get_transcript_and_store_to_rag()` - 자막 RAG 저장
- [x] `KOREAN_INVESTMENT_CHANNELS` - 한국 투자 채널 프리셋

**프리셋 채널**:
- 삼프로TV, 슈카월드, 체인지그라운드
- 박곰희TV, 에코노미스트, 한국경제TV, 머니투데이

### 파이프라인 통합 (`src/tools/pipeline_tools.py`)

ResearchPipeline용 도구 핸들러 통합:

```python
from src.tools import create_configured_pipeline, quick_research

# 방법 1: 사전 구성된 파이프라인
pipeline = create_configured_pipeline()
result = await pipeline.run(
    topic="삼성전자 투자 분석",
    symbols=["005930"],
    market="KR",
)

# 방법 2: 빠른 연구 (한 줄)
result = await quick_research(
    topic="NVDA 기술적 분석",
    symbols=["NVDA"],
    market="US",
)
```

**등록된 도구 핸들러**:
| 도구 | 함수 | 기능 |
|------|------|------|
| `stock_data` | `stock_data_handler` | 주가/종목 정보 |
| `financials` | `financials_handler` | 재무제표/비율 |
| `technical_analysis` | `technical_analysis_handler` | 기술적 지표 |
| `rag_search` | `rag_search_handler` | KB 검색 |
| `web_search` | `web_search_handler` | 웹 검색 |
| `news_search` | `news_search_handler` | 뉴스 검색 |
| `youtube` | `youtube_handler` | 유튜브 분석 |

---

## Phase 5: API 통합 ✅ 완료 (2026-01-20)

### Research Pipeline API (`src/api/routers/research.py`)

Research Pipeline을 API 엔드포인트에 연결 완료:

**레거시 엔드포인트 (하위 호환)**:
| 엔드포인트 | 설명 |
|------------|------|
| `POST /research/generate` | 기존 ResearchAgent 사용 |
| `GET /research/list` | 파일시스템 리포트 목록 |
| `WS /research/ws/{id}` | 기존 WebSocket (ping/pong) |

**파이프라인 엔드포인트 (신규)**:
| 엔드포인트 | 설명 |
|------------|------|
| `POST /research/pipeline` | 파이프라인 연구 시작 |
| `GET /research/pipeline/{id}` | 연구 상태 조회 |
| `GET /research/pipeline/list/all` | 파이프라인 연구 목록 |
| `WS /research/stream/{id}` | 실시간 진행 상황 스트리밍 |
| `DELETE /research/pipeline/{id}` | 연구 취소 |
| `GET /research/tools` | 사용 가능한 도구 목록 |

**주요 구현**:
- `ResearchJobStore`: 인메모리 연구 작업 저장소 (Pub/Sub 지원)
- `BackgroundTasks`: 비동기 파이프라인 실행
- `WebSocket Streaming`: 실시간 진행 상황 업데이트
- Pydantic 모델: `PipelineResearchRequest`, `ResearchStatusResponse` 등

**사용 예시**:
```python
# 1. 연구 시작
POST /api/v1/research/pipeline
{
  "topic": "삼성전자 2024년 실적 분석",
  "symbols": ["005930"],
  "market": "KR",
  "max_topics": 10
}
# Response: { "research_id": "pipeline_abc123...", "status": "pending" }

# 2. 상태 조회
GET /api/v1/research/pipeline/pipeline_abc123

# 3. 실시간 스트리밍 (WebSocket)
WS /api/v1/research/stream/pipeline_abc123
```

---

## Phase 6: 프론트엔드 통합 ✅ 완료 (2026-01-20)

### 타입 및 API 클라이언트

**타입 정의** (`web/types/index.ts`):
- `ResearchStatus`, `PipelineResearchRequest`, `PipelineResearchResponse`
- `ResearchStatusResponse`, `ResearchResult`, `ResearchListItem`
- WebSocket 이벤트 타입: `WSEvent`, `WSUpdateEvent`, `WSFinalEvent` 등

**API 클라이언트** (`web/lib/api.ts`):
```typescript
export const pipelineApi = {
  start: (request) => ...,      // 연구 시작
  getStatus: (id) => ...,       // 상태 조회
  list: (limit) => ...,         // 목록 조회
  cancel: (id) => ...,          // 연구 취소
  getTools: () => ...,          // 도구 목록
  createWebSocket: (id) => ..., // 실시간 스트리밍
}
```

### 컴포넌트

| 컴포넌트 | 경로 | 기능 |
|----------|------|------|
| `ResearchProgress` | `web/components/ResearchProgress.tsx` | 5단계 진행 상황 시각화, 상태별 아이콘, 상세 정보 토글 |
| `ReportViewer` | `web/components/ReportViewer.tsx` | 마크다운 리포트 렌더링, 복사/다운로드, 통계 표시 |

### 페이지

| 페이지 | 경로 | 기능 |
|--------|------|------|
| 연구 대시보드 | `web/app/research/page.tsx` | 연구 목록, 새 연구 시작 폼, 상태 필터링 |
| 연구 상세 | `web/app/research/[id]/page.tsx` | 실시간 진행 상황 (WebSocket), 리포트 뷰어 |

**주요 기능**:
- WebSocket 기반 실시간 진행 상황 업데이트
- 5단계 파이프라인 시각화 (Rephrase → Decompose → Research → Notes → Report)
- 마크다운 리포트 렌더링 및 다운로드
- 연구 취소 기능
- 반응형 디자인 (Tailwind CSS)

---

## 전체 Phase 완료 현황

| Phase | 내용 | 상태 |
|-------|------|------|
| Phase 1 | 기본 구조 설정 | ✅ 완료 |
| Phase 1.5 | Multi-provider LLM | ✅ 완료 |
| Phase 2-1 | RAG 시스템 | ✅ 완료 |
| Phase 3 | Research Pipeline | ✅ 완료 |
| Phase 4 | 추가 도구 | ✅ 완료 |
| Phase 5 | API 통합 | ✅ 완료 |
| Phase 6 | 프론트엔드 통합 | ✅ 완료 |

---

## 아키텍처 비교

| 구분 | DeepTutor | FinanceAI 현재 | FinanceAI 목표 |
|------|-----------|----------------|----------------|
| 에이전트 | 6개 모듈 | ✅ 10개 (Multi-agent) | ✅ 완료 |
| LLM | Multi-provider | ✅ Multi-provider | ✅ 완료 |
| RAG | 완전한 파이프라인 | ✅ 기본 구현 완료 | ✅ 완료 |
| Embedding | Multi-provider | ✅ Multi-provider | ✅ 완료 |
| Research | Multi-agent | ✅ Multi-agent Pipeline | ✅ 완료 |
| Tools | rag, web, paper | ✅ rag, web, youtube | ✅ 완료 |
| API | REST + WebSocket | ✅ Pipeline API | ✅ 완료 |
| Frontend | - | ✅ Research Dashboard | ✅ 완료 |

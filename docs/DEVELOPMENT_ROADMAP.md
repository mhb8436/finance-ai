# FinanceAI 개발 로드맵

> 마지막 업데이트: 2026-01-20
>
> **목적**: 프로젝트의 다음 단계 개발 사항을 구체적으로 정리하고 우선순위를 명확히 함

---

## 현재 상태 요약

### 완료된 기능 (Phase 1)

| 카테고리 | 구현 완료 항목 |
|----------|---------------|
| **에이전트** | TechnicalAgent, FundamentalAgent, ChatAgent, ResearchAgent (단순) |
| **LLM 서비스** | Multi-provider 지원 (OpenAI, Anthropic, DeepSeek, Groq, Local) |
| **데이터 도구** | stock_data, financials, indicators, news_search, web_search, youtube_tool, rag_tool (기본) |
| **API** | stock, analysis, research, chat, kb, search, youtube, system 라우터 |
| **프론트엔드** | 메인 대시보드, 종목 상세, AI 채팅 페이지 |
| **인프라** | Docker, 설정 관리, 테스트 구조 |

### 미완성 영역

- RAG 파이프라인 완성 (부분 구현됨)
- Research Pipeline (DeepTutor 패턴 미적용)
- 고급 분석 에이전트 (Sentiment, Valuation, Recommend)
- 프론트엔드 문서 관리 UI

---

## Phase 2: RAG 시스템 완성 (🔴 최우선)

### 2.1 RAG 서비스 완성

**목표**: 금융 문서 업로드 → 임베딩 → 검색이 완전히 동작하는 파이프라인

**현재 상태**: 기본 구조 존재 (`src/services/rag/`), 완성 필요

**작업 항목**:

| # | 작업 | 파일 | 의존성 | 예상 복잡도 |
|---|------|------|--------|-------------|
| 2.1.1 | RAGService 오케스트레이션 완성 | `src/services/rag/service.py` | 없음 | 중 |
| 2.1.2 | PDF 파서 금융 문서 최적화 | `src/services/rag/parsers/pdf_parser.py` | 2.1.1 | 중 |
| 2.1.3 | 시맨틱 청킹 구현 | `src/services/rag/chunkers/semantic_chunker.py` | 2.1.2 | 중 |
| 2.1.4 | 하이브리드 검색 (lexical + semantic) | `src/services/rag/retrievers/hybrid_retriever.py` | 2.1.3 | 상 |
| 2.1.5 | ChromaDB 인덱스 최적화 | `src/services/rag/retrievers/vector_retriever.py` | 2.1.3 | 중 |

**참조 코드**:
```
../DeepTutor/src/services/rag/service.py
../DeepTutor/src/services/rag/components/
```

**완료 기준**:
- [ ] PDF 문서 업로드 → 청킹 → 임베딩 → 저장 파이프라인 동작
- [ ] 자연어 쿼리로 관련 문서 청크 검색 가능
- [ ] 하이브리드 검색 (키워드 + 벡터) 동작

---

### 2.2 Knowledge Base 관리

**목표**: 사용자별 Knowledge Base 생성/관리/검색 기능

**작업 항목**:

| # | 작업 | 파일 | 의존성 | 예상 복잡도 |
|---|------|------|--------|-------------|
| 2.2.1 | KB 생성/삭제/목록 API 완성 | `src/api/routers/kb.py` | 2.1.1 | 하 |
| 2.2.2 | 문서 업로드 핸들링 | `src/api/routers/kb.py` | 2.1.2 | 중 |
| 2.2.3 | RAG 검색 엔드포인트 | `src/api/routers/kb.py` | 2.1.4 | 중 |
| 2.2.4 | 배치 문서 처리 | `src/services/rag/service.py` | 2.2.2 | 중 |

**API 엔드포인트**:
```
POST   /api/v1/kb/create              # KB 생성
GET    /api/v1/kb/list                # KB 목록
DELETE /api/v1/kb/{kb_id}             # KB 삭제
POST   /api/v1/kb/{kb_id}/upload      # 문서 업로드
POST   /api/v1/kb/{kb_id}/search      # RAG 검색
GET    /api/v1/kb/{kb_id}/documents   # 문서 목록
```

**완료 기준**:
- [ ] KB 생성/삭제 API 동작
- [ ] 파일 업로드 후 자동 처리
- [ ] 검색 API로 관련 문서 반환

---

### 2.3 임베딩 서비스 강화

**목표**: Multi-provider 임베딩 지원 및 배치 처리 최적화

**현재 상태**: 기본 구조 존재 (`src/services/embedding/`)

**작업 항목**:

| # | 작업 | 파일 | 의존성 | 예상 복잡도 |
|---|------|------|--------|-------------|
| 2.3.1 | 배치 임베딩 처리 | `src/services/embedding/client.py` | 없음 | 중 |
| 2.3.2 | 캐싱 레이어 추가 | `src/services/embedding/cache.py` | 2.3.1 | 중 |
| 2.3.3 | 로컬 임베딩 지원 (Ollama) | `src/services/embedding/adapters/local.py` | 없음 | 중 |

**완료 기준**:
- [ ] 대량 문서 배치 임베딩 처리 가능
- [ ] 동일 텍스트 재임베딩 방지 캐싱
- [ ] OpenAI / Local 임베딩 선택 가능

---

## Phase 3: Research Pipeline (🔴 높음)

### 3.1 DeepTutor 패턴 적용

**목표**: Multi-agent Research Pipeline으로 고품질 분석 리포트 생성

**현재 상태**: 단순 LLM 호출 방식의 ResearchAgent 존재

**작업 항목**:

| # | 작업 | 파일 | 의존성 | 예상 복잡도 |
|---|------|------|--------|-------------|
| 3.1.1 | 데이터 구조 정의 | `src/agents/research/data_structures.py` | 없음 | 하 |
| 3.1.2 | RephraseAgent 구현 | `src/agents/research/agents/rephrase_agent.py` | 3.1.1 | 중 |
| 3.1.3 | DecomposeAgent 구현 | `src/agents/research/agents/decompose_agent.py` | 3.1.1 | 중 |
| 3.1.4 | ManagerAgent 구현 | `src/agents/research/agents/manager_agent.py` | 3.1.1 | 상 |
| 3.1.5 | ResearchAgent 리팩토링 | `src/agents/research/agents/research_agent.py` | 3.1.1 | 중 |
| 3.1.6 | NoteAgent 구현 | `src/agents/research/agents/note_agent.py` | 3.1.5 | 중 |
| 3.1.7 | ReportAgent 구현 | `src/agents/research/agents/report_agent.py` | 3.1.6 | 중 |
| 3.1.8 | ResearchPipeline 오케스트레이터 | `src/agents/research/pipeline.py` | 3.1.2-3.1.7 | 상 |

**참조 코드**:
```
../DeepTutor/src/agents/research/research_pipeline.py
../DeepTutor/src/agents/research/agents/
```

**데이터 구조**:
```python
# src/agents/research/data_structures.py
@dataclass
class ToolTrace:
    tool_name: str
    input_params: dict
    output: Any
    timestamp: datetime

@dataclass
class TopicBlock:
    topic: str
    sub_topics: list[str]
    status: str  # pending, in_progress, completed
    notes: list[str]
    tool_traces: list[ToolTrace]

class DynamicTopicQueue:
    """동적 토픽 관리 큐"""
    pass
```

**Research Pipeline 흐름**:
```
사용자 질문
    ↓
RephraseAgent (질문 명확화)
    ↓
DecomposeAgent (분석 항목 분해)
    ↓
┌─────────────────────────────────┐
│         ManagerAgent           │
│  (흐름 관리, 도구 선택)           │
│              ↓                 │
│  ResearchAgent (실제 분석)       │
│      - 기술적 분석              │
│      - 펀더멘탈 분석            │
│      - RAG 검색                │
│      - 웹 검색                 │
│              ↓                 │
│  NoteAgent (결과 요약)          │
└─────────────────────────────────┘
    ↓
ReportAgent (최종 리포트 생성)
    ↓
종합 분석 리포트 + 인용
```

**완료 기준**:
- [ ] 6개 에이전트 개별 동작
- [ ] Pipeline 전체 흐름 동작
- [ ] 도구 사용 추적 (ToolTrace) 동작
- [ ] 인용 포함된 리포트 생성

---

### 3.2 프롬프트 관리 시스템

**목표**: YAML 기반 프롬프트 관리로 유지보수성 향상

**작업 항목**:

| # | 작업 | 파일 | 의존성 | 예상 복잡도 |
|---|------|------|--------|-------------|
| 3.2.1 | PromptManager 구현 | `src/services/prompt/manager.py` | 없음 | 중 |
| 3.2.2 | Research 프롬프트 파일 | `config/prompts/research/*.yaml` | 3.2.1 | 하 |
| 3.2.3 | Analysis 프롬프트 파일 | `config/prompts/analysis/*.yaml` | 3.2.1 | 하 |

**프롬프트 파일 구조**:
```yaml
# config/prompts/research/rephrase_agent.ko.yaml
system: |
  당신은 사용자의 주식 분석 요청을 명확하게 재구성하는 전문가입니다.
  ...

user_template: |
  원본 질문: {question}
  종목: {symbol}
  시장: {market}

  위 질문을 분석에 적합한 형태로 재구성해주세요.
```

**완료 기준**:
- [ ] YAML에서 프롬프트 로드 동작
- [ ] 다국어 지원 (ko/en)
- [ ] 변수 치환 동작

---

## Phase 4: 고급 분석 에이전트 (🟡 중간)

### 4.1 SentimentAgent

**목표**: 뉴스/유튜브 콘텐츠 기반 감성 분석

**작업 항목**:

| # | 작업 | 파일 | 의존성 | 예상 복잡도 |
|---|------|------|--------|-------------|
| 4.1.1 | SentimentAgent 기본 구현 | `src/agents/analysis/sentiment/agent.py` | 없음 | 중 |
| 4.1.2 | 뉴스 감성 분석 | `src/agents/analysis/sentiment/agent.py` | 4.1.1 | 중 |
| 4.1.3 | 유튜브 감성 분석 | `src/agents/analysis/sentiment/agent.py` | 4.1.1 | 중 |
| 4.1.4 | 종합 감성 점수 계산 | `src/agents/analysis/sentiment/agent.py` | 4.1.2, 4.1.3 | 중 |

**기능 명세**:
```python
class SentimentAgent(BaseAgent):
    async def analyze(
        self,
        symbol: str,
        market: str,
        sources: list[str] = ["news", "youtube"]
    ) -> SentimentResult:
        """
        Returns:
            SentimentResult:
                overall_score: float (-1.0 ~ 1.0)
                news_sentiment: dict
                youtube_sentiment: dict
                key_topics: list[str]
                recommendation: str (positive/neutral/negative)
        """
```

---

### 4.2 ValuationAgent

**목표**: 다양한 밸류에이션 모델로 적정 주가 산출

**작업 항목**:

| # | 작업 | 파일 | 의존성 | 예상 복잡도 |
|---|------|------|--------|-------------|
| 4.2.1 | ValuationAgent 기본 구현 | `src/agents/analysis/valuation/agent.py` | 없음 | 중 |
| 4.2.2 | DCF 모델 구현 | `src/agents/analysis/valuation/models/dcf.py` | 4.2.1 | 상 |
| 4.2.3 | 상대가치 모델 (PER, PBR) | `src/agents/analysis/valuation/models/relative.py` | 4.2.1 | 중 |
| 4.2.4 | 배당할인모델 | `src/agents/analysis/valuation/models/ddm.py` | 4.2.1 | 중 |

**기능 명세**:
```python
class ValuationAgent(BaseAgent):
    async def calculate(
        self,
        symbol: str,
        market: str,
        models: list[str] = ["dcf", "relative", "ddm"]
    ) -> ValuationResult:
        """
        Returns:
            ValuationResult:
                fair_value: float
                current_price: float
                upside_potential: float (%)
                model_results: dict[str, ModelResult]
                confidence: str (high/medium/low)
        """
```

---

### 4.3 RecommendAgent

**목표**: 모든 분석 결과를 종합한 투자 추천

**작업 항목**:

| # | 작업 | 파일 | 의존성 | 예상 복잡도 |
|---|------|------|--------|-------------|
| 4.3.1 | RecommendAgent 기본 구현 | `src/agents/recommend/agent.py` | 없음 | 중 |
| 4.3.2 | 종합 점수 계산 로직 | `src/agents/recommend/scorer.py` | 4.3.1 | 상 |
| 4.3.3 | 추천 리포트 생성 | `src/agents/recommend/agent.py` | 4.3.2 | 중 |

**의존성**: TechnicalAgent, FundamentalAgent, SentimentAgent, ValuationAgent

**기능 명세**:
```python
class RecommendAgent(BaseAgent):
    async def recommend(
        self,
        symbol: str,
        market: str,
        criteria: RecommendCriteria | None = None
    ) -> RecommendResult:
        """
        Returns:
            RecommendResult:
                recommendation: str (strong_buy/buy/hold/sell/strong_sell)
                confidence: float (0-100)
                target_price: float
                stop_loss: float
                analysis_summary: dict
                risk_factors: list[str]
                catalysts: list[str]
        """
```

---

## Phase 5: 프론트엔드 고도화 (🟡 중간)

### 5.1 문서 관리 페이지

**목표**: 문서 업로드 및 Knowledge Base 관리 UI

**작업 항목**:

| # | 작업 | 파일 | 의존성 | 예상 복잡도 |
|---|------|------|--------|-------------|
| 5.1.1 | 문서 관리 페이지 | `web/app/documents/page.tsx` | Phase 2 완료 | 중 |
| 5.1.2 | 드래그 앤 드롭 업로드 | `web/components/FileUpload.tsx` | 5.1.1 | 중 |
| 5.1.3 | KB 관리 페이지 | `web/app/knowledge/page.tsx` | 5.1.1 | 중 |
| 5.1.4 | RAG 검색 UI | `web/components/RAGSearch.tsx` | 5.1.3 | 중 |

---

### 5.2 차트 컴포넌트

**목표**: 인터랙티브 주가 차트 및 기술적 지표 시각화

**작업 항목**:

| # | 작업 | 파일 | 의존성 | 예상 복잡도 |
|---|------|------|--------|-------------|
| 5.2.1 | 캔들스틱 차트 | `web/components/charts/CandlestickChart.tsx` | 없음 | 중 |
| 5.2.2 | 기술적 지표 오버레이 | `web/components/charts/IndicatorOverlay.tsx` | 5.2.1 | 중 |
| 5.2.3 | 거래량 차트 | `web/components/charts/VolumeChart.tsx` | 5.2.1 | 하 |
| 5.2.4 | 차트 설정 패널 | `web/components/charts/ChartSettings.tsx` | 5.2.1 | 중 |

**라이브러리**: `lightweight-charts` (TradingView)

---

### 5.3 분석 결과 페이지

**목표**: 분석 결과 상세 표시 및 리포트 뷰어

**작업 항목**:

| # | 작업 | 파일 | 의존성 | 예상 복잡도 |
|---|------|------|--------|-------------|
| 5.3.1 | 기술적 분석 상세 페이지 | `web/app/analysis/technical/page.tsx` | 5.2.1 | 중 |
| 5.3.2 | 펀더멘탈 분석 상세 페이지 | `web/app/analysis/fundamental/page.tsx` | 없음 | 중 |
| 5.3.3 | 리서치 리포트 뷰어 | `web/components/ReportViewer.tsx` | Phase 3 완료 | 중 |
| 5.3.4 | 인용 표시 컴포넌트 | `web/components/Citation.tsx` | 5.3.3 | 하 |

---

## Phase 6: 통합 및 최적화 (🟢 낮음)

### 6.1 성능 최적화

| # | 작업 | 설명 |
|---|------|------|
| 6.1.1 | API 응답 캐싱 | Redis 기반 캐싱 레이어 |
| 6.1.2 | 임베딩 배치 최적화 | 대량 문서 처리 속도 개선 |
| 6.1.3 | 프론트엔드 번들 최적화 | 코드 스플리팅, 레이지 로딩 |

### 6.2 추가 기능

| # | 작업 | 설명 |
|---|------|------|
| 6.2.1 | 실시간 뉴스 피드 | WebSocket 기반 실시간 뉴스 |
| 6.2.2 | 포트폴리오 추적 | 사용자 포트폴리오 관리 |
| 6.2.3 | 알림 시스템 | 가격 알림, 분석 완료 알림 |

### 6.3 테스트 및 문서화

| # | 작업 | 설명 |
|---|------|------|
| 6.3.1 | E2E 테스트 작성 | Playwright 기반 E2E 테스트 |
| 6.3.2 | API 문서 보강 | OpenAPI 스펙 상세화 |
| 6.3.3 | 사용자 가이드 | 기능별 사용자 가이드 |

---

## 의존성 요약

```
Phase 2 (RAG) ─────────────────────────────────────────┐
    │                                                   │
    ├── 2.1 RAG 서비스 ────┬─── 2.2 KB 관리            │
    │                      │                           │
    └── 2.3 임베딩 서비스 ──┘                           │
                                                        │
Phase 3 (Research) ─────────────────────────────────────┤
    │                                                   │
    ├── 3.1 Research Pipeline (Phase 2 의존)            │
    │                                                   │
    └── 3.2 프롬프트 관리                               │
                                                        │
Phase 4 (고급 분석) ────────────────────────────────────┤
    │                                                   │
    ├── 4.1 SentimentAgent                             │
    │                                                   │
    ├── 4.2 ValuationAgent                             │
    │                                                   │
    └── 4.3 RecommendAgent (4.1, 4.2 의존)              │
                                                        │
Phase 5 (프론트엔드) ───────────────────────────────────┤
    │                                                   │
    ├── 5.1 문서 관리 (Phase 2 의존)                    │
    │                                                   │
    ├── 5.2 차트 컴포넌트                               │
    │                                                   │
    └── 5.3 분석 페이지 (Phase 3 의존)                  │
                                                        │
Phase 6 (최적화) ───────────────────────────────────────┘
```

---

## 추가 필요 의존성

```txt
# requirements.txt 추가 예정
sentence-transformers>=2.2.0   # 로컬 임베딩 (선택)
redis>=5.0.0                   # 캐싱 (Phase 6)
playwright>=1.40.0             # E2E 테스트 (Phase 6)
```

```json
// web/package.json 추가 예정
{
  "dependencies": {
    "lightweight-charts": "^4.1.0",
    "react-dropzone": "^14.2.0"
  }
}
```

---

## 마일스톤 체크리스트

### Phase 2 완료 기준
- [ ] PDF 문서 업로드 → RAG 검색 전체 파이프라인 동작
- [ ] KB API 모든 엔드포인트 동작
- [ ] 프론트엔드에서 문서 업로드/검색 가능

### Phase 3 완료 기준
- [ ] 6개 Research 에이전트 개별 테스트 통과
- [ ] Research Pipeline 전체 흐름 동작
- [ ] 인용 포함된 분석 리포트 생성

### Phase 4 완료 기준
- [ ] SentimentAgent 뉴스/유튜브 감성 분석 동작
- [ ] ValuationAgent 적정가 산출 동작
- [ ] RecommendAgent 종합 추천 동작

### Phase 5 완료 기준
- [ ] 문서 관리 UI 완성
- [ ] 인터랙티브 차트 동작
- [ ] 분석 결과 상세 페이지 완성

---

## 참고 자료

| 자료 | 경로 |
|------|------|
| DeepTutor Research Pipeline | `../DeepTutor/src/agents/research/` |
| DeepTutor RAG Service | `../DeepTutor/src/services/rag/` |
| DeepTutor Embedding | `../DeepTutor/src/services/embedding/` |
| 프로젝트 비전 | `docs/VISION.md` |
| 현재 상태 | `docs/PROJECT_STATUS.md` |
| 아키텍처 | `docs/ARCHITECTURE.md` |

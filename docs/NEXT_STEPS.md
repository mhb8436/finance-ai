# FinanceAI 다음 단계 작업

> 우선순위: 🔴 높음 | 🟡 중간 | 🟢 낮음
>
> **🎯 목표 비전**: `docs/VISION.md` 참조

---

## 🔴 최우선: RAG 시스템 구축 (Phase 2-1)

### 1. RAG 서비스 구현

**참조**: `../DeepTutor/src/services/rag/`

```
src/services/rag/
├── __init__.py
├── service.py              # RAGService 메인 클래스
├── factory.py              # Pipeline factory
└── components/
    ├── parsers/
    │   ├── base.py
    │   ├── pdf_parser.py   # PDF 파싱
    │   └── text_parser.py  # 텍스트 파싱
    ├── chunkers/
    │   ├── base.py
    │   └── semantic_chunker.py
    ├── embedders/
    │   ├── base.py
    │   └── openai_embedder.py
    ├── indexers/
    │   ├── base.py
    │   └── vector_index.py
    └── retrievers/
        ├── base.py
        └── hybrid_retriever.py
```

**작업 목록**:
- [ ] RAGService 클래스 구현
- [ ] PDF 파서 구현 (PyPDF2 or pdfplumber)
- [ ] Semantic chunker 구현
- [ ] OpenAI embedder 구현
- [ ] Vector index 구현 (ChromaDB or FAISS)
- [ ] Hybrid retriever 구현

### 2. 임베딩 서비스 구현

**참조**: `../DeepTutor/src/services/embedding/`

```
src/services/embedding/
├── __init__.py
├── client.py               # EmbeddingClient
└── adapters/
    ├── base.py
    ├── openai.py           # OpenAI embeddings
    └── local.py            # Ollama embeddings
```

**작업 목록**:
- [ ] EmbeddingClient 구현
- [ ] OpenAI adapter 구현
- [ ] Local adapter 구현 (Ollama)

### 3. Knowledge Base API

```
src/api/routers/knowledge.py
```

**엔드포인트**:
```
POST /api/v1/knowledge/create          # KB 생성
GET  /api/v1/knowledge/list            # KB 목록
DELETE /api/v1/knowledge/{kb_name}     # KB 삭제
POST /api/v1/knowledge/{kb_name}/upload  # 문서 업로드
POST /api/v1/knowledge/{kb_name}/search  # RAG 검색
```

### 4. RAG 도구 구현

```python
# src/tools/rag_tool.py
async def rag_search(
    query: str,
    kb_name: str,
    mode: str = "hybrid"  # hybrid, local, global
) -> dict:
    """Knowledge base에서 검색"""
    pass
```

---

## 🔴 높음: 추가 도구 구현 (Phase 2-2)

### 5. 웹 검색 도구

**참조**: `../DeepTutor/src/tools/web_search.py`

```python
# src/tools/web_search.py
async def web_search(
    query: str,
    provider: str = "serper"  # serper, tavily
) -> list[dict]:
    """웹 검색 수행"""
    pass
```

**작업 목록**:
- [ ] Serper API 연동
- [ ] Tavily API 연동
- [ ] 검색 결과 정규화

### 6. 유튜브 도구

```python
# src/tools/youtube_tool.py
from youtube_transcript_api import YouTubeTranscriptApi

async def get_youtube_transcript(
    video_id: str,
    language: str = "ko"
) -> str:
    """유튜브 영상 스크립트 추출"""
    pass

async def search_channel_videos(
    channel_id: str,
    query: str | None = None
) -> list[dict]:
    """채널 영상 검색"""
    pass
```

**의존성**: `youtube-transcript-api`

---

## 🟡 중간: Research Pipeline (Phase 2-3)

### 7. Research Pipeline 구현

**참조**: `../DeepTutor/src/agents/research/`

```
src/agents/research/
├── pipeline.py             # ResearchPipeline
├── data_structures.py      # ToolTrace, TopicBlock, DynamicTopicQueue
└── agents/
    ├── rephrase_agent.py   # 주제 명확화
    ├── decompose_agent.py  # 주제 분해
    ├── manager_agent.py    # 흐름 관리
    ├── research_agent.py   # 실제 리서치
    ├── note_agent.py       # 요약
    └── report_agent.py     # 리포트 생성
```

**작업 목록**:
- [ ] DynamicTopicQueue 구현
- [ ] ToolTrace, TopicBlock 데이터 구조
- [ ] 6개 Research agents 구현
- [ ] ResearchPipeline orchestrator

### 8. 프롬프트 관리 서비스

**참조**: `../DeepTutor/src/services/prompt/`

```
src/services/prompt/
├── __init__.py
└── manager.py              # PromptManager

config/prompts/
├── research/
│   ├── rephrase_agent.ko.yaml
│   ├── decompose_agent.ko.yaml
│   └── ...
└── analysis/
    └── ...
```

---

## 🟡 중간: 프론트엔드 기능 (Phase 2-4)

### 9. 문서 관리 페이지

```
web/app/documents/page.tsx      # 문서 업로드/관리
web/app/knowledge/page.tsx      # Knowledge Base 관리
```

**기능**:
- [ ] 파일 업로드 (드래그 앤 드롭)
- [ ] KB 생성/삭제
- [ ] 문서 목록 표시
- [ ] RAG 검색 인터페이스

### 10. 차트 구현

**파일**: `web/components/StockChart.tsx`

```tsx
import { createChart } from 'lightweight-charts'

export function StockChart({ data }: { data: PriceData[] }) {
  // 캔들스틱 차트 구현
}
```

**작업 목록**:
- [ ] 캔들스틱 차트
- [ ] 기술적 지표 오버레이
- [ ] 거래량 차트

### 11. 분석 페이지

```
web/app/analysis/technical/page.tsx
web/app/analysis/fundamental/page.tsx
```

---

## 🟢 낮음: 고급 기능 (Phase 3)

### 12. Sentiment Agent

```python
# src/agents/analysis/sentiment/agent.py
class SentimentAgent(BaseAgent):
    """뉴스/유튜브 감성 분석"""
    async def analyze(self, texts: list[str]) -> dict:
        pass
```

### 13. Valuation Agent

```python
# src/agents/analysis/valuation/agent.py
class ValuationAgent(BaseAgent):
    """적정가 산출"""
    async def calculate(self, symbol: str, market: str) -> dict:
        pass
```

### 14. Recommend Agent

```python
# src/agents/recommend/agent.py
class RecommendAgent(BaseAgent):
    """종합 종목 추천"""
    async def recommend(self, criteria: dict) -> list[dict]:
        pass
```

---

## 의존성 추가 필요

```txt
# requirements.txt 추가
chromadb>=0.4.0           # 벡터 DB
pdfplumber>=0.10.0        # PDF 파싱
youtube-transcript-api>=0.6.0  # 유튜브 스크립트
tavily-python>=0.3.0      # Tavily 검색 (선택)
```

---

## 참고 파일 위치

| 작업 | DeepTutor 참조 | FinanceAI 대상 |
|------|---------------|---------------|
| RAG Service | `../DeepTutor/src/services/rag/service.py` | `src/services/rag/service.py` |
| Embedding | `../DeepTutor/src/services/embedding/client.py` | `src/services/embedding/client.py` |
| Research Pipeline | `../DeepTutor/src/agents/research/research_pipeline.py` | `src/agents/research/pipeline.py` |
| Web Search | `../DeepTutor/src/tools/web_search.py` | `src/tools/web_search.py` |
| RAG Tool | `../DeepTutor/src/tools/rag_tool.py` | `src/tools/rag_tool.py` |
| Prompt Manager | `../DeepTutor/src/services/prompt/manager.py` | `src/services/prompt/manager.py` |

---

## Quick Start (현재)

```bash
# 1. 환경 변수 설정
cp .env.example .env
# .env 편집하여 LLM_API_KEY 입력

# 2. 의존성 설치
pip install -r requirements.txt
cd web && npm install && cd ..

# 3. 실행
python scripts/start_web.py
```

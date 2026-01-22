# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 긴급 TODO (우선 확인)

**`docs/TODO.md` 파일을 먼저 확인하세요!** 진행 중인 작업과 다음 단계가 기록되어 있습니다.

현재 이슈: YouTube RAG 임베딩 오류 - Azure 배포 설정 필요

## Project Overview

FinanceAI is an AI-powered stock analysis platform supporting Korean (KRX) and US (NYSE/NASDAQ) markets. It provides technical analysis, fundamental analysis, AI-powered Q&A, and automated research report generation.

**Tech Stack**: FastAPI backend (Python 3.10+), Next.js 15 frontend (React 19, TypeScript), Tailwind CSS, Docker

## Git 커밋 규칙

- **Claude를 Co-Author 또는 Contributor로 추가 금지**: 커밋 메시지에 `Co-Authored-By: Claude` 또는 유사한 형태로 Claude를 기여자로 표시하지 않습니다.
- 커밋 메시지는 변경 내용을 명확하게 설명하되, AI 도구 사용 여부는 명시하지 않습니다.

## 🎯 프로젝트 비전 (중요!)

**목표**: Google NotebookLM처럼 다양한 데이터 소스(문서, 웹, 유튜브, 주가)를 조합하여 AI 에이전트로 종목을 분석하고 추천하는 시스템

**상세 비전 및 로드맵**: `docs/VISION.md` 참조

### 목표 데이터 소스
- 📄 사용자 문서 (PDF, 리포트, 공시자료) → RAG
- 🌐 웹 검색 (뉴스, 증권사 리포트)
- 📺 유튜브 채널 스크립트 → 분석
- 📊 실시간 주가/재무 데이터
- 📰 뉴스 피드

### 현재 vs 목표

| 구분 | 현재 | 목표 |
|------|------|------|
| 에이전트 | 4개 (단순) | 10+ (Multi-agent) |
| RAG | ❌ 없음 | ✅ 금융 문서 RAG |
| Research | 단순 LLM | DeepTutor 패턴 |
| Tools | 주가/재무만 | + RAG, Web, YouTube |

## Reference Codebase

이 프로젝트는 **DeepTutor** 코드베이스를 기반으로 만들어졌습니다. 새로운 기능 개발이나 구조 변경 시 항상 상위 디렉토리의 DeepTutor 프로젝트(`../DeepTutor/`)를 참고하세요.

- 아키텍처 패턴, 코드 스타일, 설정 구조 등은 DeepTutor의 방식을 따릅니다
- 유사한 기능 구현 시 DeepTutor의 해당 코드를 먼저 확인하세요

### DeepTutor 핵심 참조 위치

| 기능 | DeepTutor 경로 | 설명 |
|------|---------------|------|
| **Research Pipeline** | `../DeepTutor/src/agents/research/` | Multi-agent orchestration |
| **RAG Service** | `../DeepTutor/src/services/rag/` | 파싱→청킹→임베딩→검색 |
| **Embedding Service** | `../DeepTutor/src/services/embedding/` | Multi-provider embeddings |
| **Prompt Manager** | `../DeepTutor/src/services/prompt/` | 프롬프트 관리 |
| **Web Search Tool** | `../DeepTutor/src/tools/web_search.py` | 웹 검색 |
| **RAG Tool** | `../DeepTutor/src/tools/rag_tool.py` | RAG 검색 도구 |

## Common Commands

### Development
```bash
# Start full application (frontend + backend)
python scripts/start_web.py

# Start backend only
python scripts/run_server.py
# Or: uvicorn src.api.main:app --host 0.0.0.0 --port 8001 --reload

# Start frontend only (from web/ directory)
cd web && npm run dev
```

### Docker
```bash
docker compose up                    # Build and run
docker compose --profile dev up      # Dev mode with hot-reload
```

### Testing & Linting
```bash
pytest tests/                        # Run all tests
pytest tests/test_file.py::test_name # Run single test
ruff check src/                      # Lint backend code
ruff check src/ --fix                # Auto-fix lint issues
```

### Frontend (from web/ directory)
```bash
npm install                          # Install dependencies
npm run dev                          # Development server
npm run build                        # Production build
npm run lint                         # Lint frontend code
```

## Required Environment Variables

Copy `.env.example` to `.env` and set these required values:
```
LLM_MODEL=gpt-4o
LLM_API_KEY=sk-...
LLM_HOST=https://api.openai.com/v1
```

Optional: `OPENDART_API_KEY` (Korean financials), `SEARCH_API_KEY` + `SEARCH_PROVIDER` (news search)

## Architecture

### Backend Structure (`src/`)

**Agent Modules** (`src/agents/`): All agents inherit from `BaseAgent` in `base_agent.py`
- `technical/` - Technical analysis (indicators, patterns)
- `fundamental/` - Fundamental analysis (financials, ratios)
- `research/` - Research report generation
- `chat/` - AI-powered Q&A with tool calling

**Tools** (`src/tools/`): Data fetching utilities
- `stock_data.py` - Stock price and info (yfinance, pykrx)
- `financials.py` - Financial statements and ratios
- `indicators.py` - Technical indicator calculations
- `news_search.py` - News search integration

**API** (`src/api/`): FastAPI routers
- `/api/v1/stock` - Stock data endpoints
- `/api/v1/analysis` - Technical/fundamental analysis
- `/api/v1/research` - Research report generation
- `/api/v1/chat` - AI Q&A endpoints

### Frontend Structure (`web/`)

- `app/` - Next.js App Router pages
- `app/stock/[symbol]/` - Stock detail page
- `app/chat/` - AI chat interface

### Configuration

- `config/main.yaml` - System settings, indicator defaults
- `config/agents.yaml` - LLM parameters per agent
- `.env` - API keys and endpoints

## Data Sources

| Market | Price Data | Financials |
|--------|------------|------------|
| US | yfinance | yfinance |
| KR | pykrx | OpenDART API |

## Key Patterns

**BaseAgent**: All agents inherit from `src/agents/base_agent.py`. Implement the abstract `process()` method. Use `call_llm()` for standard completions or `stream_llm()` for streaming. Pass `tools` parameter to `call_llm()` for function calling.

**Tool Functions**: Async functions in `src/tools/` for data fetching. Support both US and KR markets via `market` parameter ("US" or "KR").

**API Structure**: RESTful endpoints with Pydantic models for request/response validation.

**Adding a New Agent**: Create directory under `src/agents/`, inherit from `BaseAgent`, implement `process()` method. See `src/agents/chat/agent.py` for tool-calling pattern with OpenAI function definitions.

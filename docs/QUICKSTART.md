# FinanceAI 빠른 시작 가이드

## 사전 요구사항

- Python 3.10 이상
- Node.js 18 이상
- OpenAI API 키

## 1. 환경 설정

```bash
# 프로젝트 디렉토리로 이동
cd /Users/mhb8436/Workspaces/FinanceAI

# 환경 변수 파일 생성
cp .env.example .env
```

`.env` 파일을 편집하여 API 키 입력:

```bash
# 필수
LLM_API_KEY=sk-your-openai-api-key-here

# 선택 (한국 주식 재무정보용)
OPENDART_API_KEY=your-opendart-api-key
```

## 2. 의존성 설치

```bash
# Python 가상환경 (권장)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Python 패키지 설치
pip install -r requirements.txt

# 프론트엔드 패키지 설치
cd web
npm install
cd ..
```

## 3. 실행

```bash
# 전체 실행 (백엔드 + 프론트엔드)
python scripts/start_web.py
```

또는 별도 실행:

```bash
# 터미널 1: 백엔드
python scripts/run_server.py

# 터미널 2: 프론트엔드
cd web && npm run dev
```

## 4. 접속

- **프론트엔드**: http://localhost:3000
- **API 문서**: http://localhost:8001/docs

## 5. 테스트

### 종목 검색
홈페이지에서 종목 코드 입력 (예: `AAPL`, `005930`)

### AI 채팅
`/chat` 페이지에서 질문:
- "삼성전자 현재 주가 알려줘"
- "AAPL의 PER은 얼마야?"
- "테슬라 최근 뉴스 있어?"

### API 직접 호출

```bash
# 주가 조회
curl "http://localhost:8001/api/v1/stock/price/AAPL?market=US&period=1mo"

# 종목 정보
curl "http://localhost:8001/api/v1/stock/info/AAPL?market=US"

# 기술적 분석
curl -X POST "http://localhost:8001/api/v1/analysis/technical" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "market": "US"}'

# AI 채팅
curl -X POST "http://localhost:8001/api/v1/chat/query" \
  -H "Content-Type: application/json" \
  -d '{"message": "애플 주가 분석해줘"}'
```

## 6. Docker 실행 (대안)

```bash
# 빌드 및 실행
docker compose up

# 백그라운드 실행
docker compose up -d

# 로그 확인
docker compose logs -f

# 중지
docker compose down
```

## 문제 해결

### 포트 충돌
`.env` 파일에서 포트 변경:
```
BACKEND_PORT=8002
FRONTEND_PORT=3001
```

### API 키 오류
`.env` 파일의 `LLM_API_KEY` 확인

### 한국 주식 데이터 오류
pykrx 설치 확인: `pip install pykrx`

### 프론트엔드 빌드 오류
```bash
cd web
rm -rf node_modules .next
npm install
npm run dev
```

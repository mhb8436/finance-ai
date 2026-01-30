# FinanceAI

AI 기반 주식 분석 플랫폼 - 한국(KRX) 및 미국(NYSE/NASDAQ) 시장 지원

## 데모

![FinanceAI Demo](docs/screenshots/demo.gif)

## 주요 기능

- **주식 검색 및 차트** - 실시간 주가, 캔들차트, 기업 정보
- **기술적 분석** - 이동평균, RSI, MACD 등 기술 지표 + AI 해석
- **기본적 분석** - 재무제표, 밸류에이션, 재무비율 + AI 해석
- **AI 리서치** - 멀티 에이전트 기반 종합 투자 리포트 자동 생성
- **AI 채팅** - 자연어로 주식 정보 질의응답

## 기술 스택

- **Backend**: FastAPI, Python 3.10+
- **Frontend**: Next.js 15, React 19, TypeScript, Tailwind CSS
- **AI**: OpenAI GPT-4 (LangChain)
- **Data**: yfinance, pykrx, OpenDART

## 빠른 시작

```bash
# 저장소 클론
git clone https://github.com/mhb8436/FinanceAI.git
cd FinanceAI

# 환경 변수 설정
cp .env.example .env
# .env 파일에 LLM_API_KEY 등 설정

# 실행 (Docker)
docker compose up

# 또는 수동 실행
python scripts/start_web.py
```

- 프론트엔드: http://localhost:3000
- API 문서: http://localhost:8001/docs

## 샘플 리포트

AI 리서치 기능으로 생성된 실제 분석 리포트 예시입니다.

### 삼성전자 (005930.KS)
> **권고: 선별적 매수(Selective Buy)**
> Forward P/E ≈ 8.7, EV/EBITDA ≈ 13.4
> 메모리 ASP 회복 및 파운드리 성장 시 의미 있는 상승 여지 존재

📄 [전체 리포트 보기](docs/examples/samsung_005930_research_report.md)

### 네이버 (035420.KS)
> **권고: 중립(보유)**
> Forward P/E ≈ 19.6x, EV/EBITDA ≈ 14x
> 12개월 목표주가: 상단 375,000원 / 기준 310,000원 / 하단 235,000원

📄 [전체 리포트 보기](docs/examples/naver_035420_research_report.md)

### 호텔신라 (008770.KS)
> **권고: Hold (중립)**
> 목표주가: Bear 34,000원 / Base 46,000원 / Bull 60,000원
> 면세사업 회복세, 호텔·레저 부문 실적 개선 중

📄 [전체 리포트 보기](docs/examples/hotelshilla_008770_research_report.md)

### Salesforce (CRM)
> **권고: HOLD (중립)**
> 총마진 77%, FCF $12.43bn
> AI 솔루션 전환 및 Data Cloud 성장 주목

📄 [전체 리포트 보기](docs/examples/salesforce_CRM_research_report.md)

## 문서

- [프로젝트 비전](docs/VISION.md)
- [통합 테스트 시나리오](docs/INTEGRATION_TEST_SCENARIO.md)
- [샘플 리포트](docs/examples/)

## 라이선스

MIT License

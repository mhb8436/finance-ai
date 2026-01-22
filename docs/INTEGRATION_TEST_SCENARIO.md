# AI 종목 리서치 시스템 통합테스트 시나리오

## 테스트 환경

| 항목 | 설정 |
|------|------|
| Backend | http://localhost:8001 |
| Frontend | http://localhost:3000 |
| LLM Provider | Azure OpenAI (gpt-5-mini) |
| Database | In-memory (테스트용) |

---

## 1. 사전 조건 확인

### TC-001: 서버 상태 확인
**목적**: 백엔드/프론트엔드 서버 정상 동작 확인

| 단계 | 동작 | 예상 결과 |
|------|------|-----------|
| 1 | `GET http://localhost:8001/health` 호출 | `{"status": "healthy"}` 반환 |
| 2 | `GET http://localhost:8001/docs` 접속 | Swagger UI 표시 |
| 3 | `http://localhost:3000` 접속 | FinanceAI 메인 페이지 로드 |
| 4 | `http://localhost:3000/research` 접속 | AI 종목 리서치 페이지 로드 |

### TC-002: Azure OpenAI 연결 확인
**목적**: LLM 서비스 연결 상태 확인

| 단계 | 동작 | 예상 결과 |
|------|------|-----------|
| 1 | Backend 로그 확인 | Azure OpenAI 초기화 성공 메시지 |
| 2 | `GET /api/v1/pipeline/tools` 호출 | 사용 가능한 도구 목록 반환 |

---

## 2. API 엔드포인트 테스트

### TC-010: 리서치 목록 조회 (빈 상태)
**목적**: 초기 상태에서 리서치 목록 조회

```bash
curl -X GET http://localhost:8001/api/v1/pipeline/research
```

| 단계 | 동작 | 예상 결과 |
|------|------|-----------|
| 1 | GET 요청 | HTTP 200 |
| 2 | 응답 확인 | `[]` (빈 배열) |

### TC-011: 새 리서치 시작 (미국 주식)
**목적**: 미국 주식 분석 리서치 생성

```bash
curl -X POST http://localhost:8001/api/v1/pipeline/research \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "애플(AAPL) 2024년 실적 분석 및 투자 전망",
    "symbols": ["AAPL"],
    "market": "US",
    "context": "AI 사업 확장 관점에서 분석",
    "max_topics": 5
  }'
```

| 단계 | 동작 | 예상 결과 |
|------|------|-----------|
| 1 | POST 요청 | HTTP 202 (Accepted) |
| 2 | 응답 확인 | `research_id` 포함된 JSON 반환 |
| 3 | 상태 확인 | `status: "pending"` 또는 `"running"` |

**예상 응답:**
```json
{
  "research_id": "uuid-xxxx-xxxx",
  "topic": "애플(AAPL) 2024년 실적 분석 및 투자 전망",
  "status": "pending",
  "created_at": "2024-xx-xxTxx:xx:xx"
}
```

### TC-012: 새 리서치 시작 (한국 주식)
**목적**: 한국 주식 분석 리서치 생성

```bash
curl -X POST http://localhost:8001/api/v1/pipeline/research \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "삼성전자(005930) 반도체 사업 분석",
    "symbols": ["005930"],
    "market": "KR",
    "max_topics": 5
  }'
```

| 단계 | 동작 | 예상 결과 |
|------|------|-----------|
| 1 | POST 요청 | HTTP 202 |
| 2 | 응답 확인 | `research_id` 반환 |

### TC-013: 리서치 상태 조회
**목적**: 진행 중인 리서치 상태 확인

```bash
curl -X GET http://localhost:8001/api/v1/pipeline/research/{research_id}/status
```

| 단계 | 동작 | 예상 결과 |
|------|------|-----------|
| 1 | GET 요청 | HTTP 200 |
| 2 | 응답 확인 | `status`, `current_stage`, `progress` 포함 |

**예상 응답 (진행 중):**
```json
{
  "research_id": "uuid-xxxx",
  "topic": "...",
  "status": "running",
  "current_stage": "research",
  "progress": {
    "stage": "research",
    "event": "데이터 수집 중...",
    "details": {}
  }
}
```

### TC-014: 리서치 취소
**목적**: 진행 중인 리서치 취소

```bash
curl -X POST http://localhost:8001/api/v1/pipeline/research/{research_id}/cancel
```

| 단계 | 동작 | 예상 결과 |
|------|------|-----------|
| 1 | POST 요청 | HTTP 200 |
| 2 | 상태 확인 | `status: "cancelled"` |

### TC-015: 존재하지 않는 리서치 조회
**목적**: 에러 처리 확인

```bash
curl -X GET http://localhost:8001/api/v1/pipeline/research/invalid-id/status
```

| 단계 | 동작 | 예상 결과 |
|------|------|-----------|
| 1 | GET 요청 | HTTP 404 |
| 2 | 응답 확인 | 에러 메시지 반환 |

---

## 3. WebSocket 실시간 업데이트 테스트

### TC-020: WebSocket 연결
**목적**: 실시간 진행 상황 수신 확인

```javascript
const ws = new WebSocket('ws://localhost:8001/api/v1/pipeline/research/{research_id}/ws');

ws.onmessage = (event) => {
  console.log(JSON.parse(event.data));
};
```

| 단계 | 동작 | 예상 결과 |
|------|------|-----------|
| 1 | WebSocket 연결 | `type: "connected"` 메시지 수신 |
| 2 | 초기 상태 | `type: "current_state"` 메시지 수신 |
| 3 | 진행 업데이트 | `type: "update"` 메시지 주기적 수신 |
| 4 | 완료 시 | `type: "final"` 메시지 수신 |
| 5 | 하트비트 | `type: "heartbeat"` 30초 간격 수신 |

**예상 메시지 시퀀스:**
```json
// 1. 연결 확인
{"type": "connected", "research_id": "uuid-xxxx"}

// 2. 현재 상태
{"type": "current_state", "data": {...}}

// 3. 진행 업데이트 (반복)
{"type": "update", "data": {"status": "running", "current_stage": "research", ...}}

// 4. 완료
{"type": "final", "status": "completed", "result": {...}}
```

### TC-021: WebSocket 에러 처리
**목적**: 잘못된 research_id로 연결 시 에러 처리

| 단계 | 동작 | 예상 결과 |
|------|------|-----------|
| 1 | 잘못된 ID로 연결 | `type: "error"` 메시지 수신 |
| 2 | 연결 종료 | WebSocket 자동 close |

---

## 4. 프론트엔드 UI 테스트

### TC-030: 리서치 목록 페이지
**URL**: `http://localhost:3000/research`

| 단계 | 동작 | 예상 결과 |
|------|------|-----------|
| 1 | 페이지 로드 | "AI 종목 리서치" 헤더 표시 |
| 2 | 빈 상태 확인 | "아직 리서치 리포트가 없습니다" 메시지 |
| 3 | 새로고침 버튼 클릭 | 목록 갱신 (로딩 스피너 표시) |
| 4 | "+ 새 분석 시작" 클릭 | 새 분석 폼 표시 |

### TC-031: 새 분석 폼 입력
**URL**: `http://localhost:3000/research`

| 단계 | 동작 | 예상 결과 |
|------|------|-----------|
| 1 | "+ 새 분석 시작" 클릭 | 폼 영역 확장 |
| 2 | 분석 주제 입력 | "삼성전자 투자 분석" |
| 3 | 종목 코드 입력 | "005930" |
| 4 | 시장 선택 | "한국 (KRX)" 선택 |
| 5 | 분석 상세도 조절 | 슬라이더로 5 설정 |
| 6 | "분석 시작" 클릭 | 상세 페이지로 이동 |

### TC-032: 분석 상세 페이지 - 진행 중
**URL**: `http://localhost:3000/research/{research_id}`

| 단계 | 동작 | 예상 결과 |
|------|------|-----------|
| 1 | 페이지 로드 | 분석 주제 표시 |
| 2 | 실시간 연결 | "실시간 연결" 녹색 표시 |
| 3 | 진행 상황 | 5단계 진행바 표시 |
| 4 | 현재 단계 | 진행 중인 단계 스피너 표시 |
| 5 | 단계 클릭 | 상세 정보 확장 |

### TC-033: 분석 상세 페이지 - 완료
**URL**: `http://localhost:3000/research/{research_id}`

| 단계 | 동작 | 예상 결과 |
|------|------|-----------|
| 1 | 완료 상태 | 진행바 100%, 녹색 |
| 2 | 리포트 표시 | Markdown 렌더링된 리포트 |
| 3 | 복사 버튼 | 클립보드에 복사 |
| 4 | 다운로드 버튼 | .md 파일 다운로드 |
| 5 | 통계 표시 | 토큰 수, 단어 수 등 |

### TC-034: 분석 취소
**URL**: `http://localhost:3000/research/{research_id}`

| 단계 | 동작 | 예상 결과 |
|------|------|-----------|
| 1 | 진행 중 상태 | "취소" 버튼 표시 |
| 2 | 취소 버튼 클릭 | 확인 다이얼로그 |
| 3 | 확인 | 상태 "취소됨"으로 변경 |
| 4 | 취소 후 | 취소 버튼 비활성화 |

---

## 5. End-to-End 시나리오 테스트

### TC-050: 전체 플로우 - 미국 주식 분석
**목적**: 사용자 관점에서 전체 흐름 검증

| 단계 | 동작 | 예상 결과 |
|------|------|-----------|
| 1 | `/research` 페이지 접속 | 리서치 목록 페이지 로드 |
| 2 | "+ 새 분석 시작" 클릭 | 폼 표시 |
| 3 | 주제: "테슬라 전기차 시장 분석" 입력 | - |
| 4 | 종목: "TSLA" 입력 | - |
| 5 | 시장: "미국" 선택 | - |
| 6 | 상세도: 5 설정 | - |
| 7 | "분석 시작" 클릭 | 상세 페이지로 이동 |
| 8 | 실시간 연결 확인 | 녹색 "실시간 연결" 표시 |
| 9 | 진행 단계 확인 | 1~5단계 순차 진행 |
| 10 | 완료 대기 | 리포트 생성 완료 |
| 11 | 리포트 내용 확인 | 테슬라 분석 내용 포함 |
| 12 | 다운로드 | .md 파일 저장 |
| 13 | 목록으로 이동 | "완료" 상태로 표시 |

### TC-051: 전체 플로우 - 한국 주식 분석
**목적**: 한국 시장 데이터 연동 검증

| 단계 | 동작 | 예상 결과 |
|------|------|-----------|
| 1 | 주제: "삼성전자 반도체 경쟁력 분석" | - |
| 2 | 종목: "005930, 000660" | 삼성전자, SK하이닉스 |
| 3 | 시장: "한국 (KRX)" | - |
| 4 | 분석 완료 | KRX 데이터 기반 리포트 |

### TC-052: 동시 분석 실행
**목적**: 복수 리서치 동시 처리 검증

| 단계 | 동작 | 예상 결과 |
|------|------|-----------|
| 1 | 첫 번째 분석 시작 | AAPL 분석 |
| 2 | 두 번째 분석 시작 | MSFT 분석 |
| 3 | 목록 확인 | 2개 "진행중" 상태 |
| 4 | 각각 완료 대기 | 독립적으로 완료 |

### TC-053: 에러 복구 시나리오
**목적**: 오류 상황 처리 검증

| 단계 | 동작 | 예상 결과 |
|------|------|-----------|
| 1 | 잘못된 종목 코드 입력 | "INVALID123" |
| 2 | 분석 시작 | 에러 또는 부분 결과 |
| 3 | 에러 메시지 확인 | 사용자 친화적 메시지 |
| 4 | 재시도 가능 | 새 분석 시작 가능 |

---

## 6. 성능 테스트

### TC-060: 응답 시간 측정

| 항목 | 목표 |
|------|------|
| 페이지 로드 | < 2초 |
| API 응답 (목록) | < 500ms |
| WebSocket 연결 | < 1초 |
| 분석 시작 응답 | < 1초 |

### TC-061: 리소스 사용량

| 항목 | 모니터링 |
|------|----------|
| 메모리 | Backend 메모리 사용량 |
| CPU | 분석 중 CPU 사용률 |
| 네트워크 | WebSocket 트래픽 |

---

## 7. 테스트 데이터

### 미국 주식 테스트 케이스
```json
[
  {"symbol": "AAPL", "name": "Apple Inc."},
  {"symbol": "MSFT", "name": "Microsoft Corporation"},
  {"symbol": "TSLA", "name": "Tesla Inc."},
  {"symbol": "NVDA", "name": "NVIDIA Corporation"},
  {"symbol": "GOOGL", "name": "Alphabet Inc."}
]
```

### 한국 주식 테스트 케이스
```json
[
  {"symbol": "005930", "name": "삼성전자"},
  {"symbol": "000660", "name": "SK하이닉스"},
  {"symbol": "035420", "name": "NAVER"},
  {"symbol": "035720", "name": "카카오"},
  {"symbol": "051910", "name": "LG화학"}
]
```

---

## 8. 체크리스트

### 기능 테스트
- [x] TC-001: 서버 상태 확인 ✅ PASS
- [x] TC-002: Azure OpenAI 연결 확인 ✅ PASS (버그 수정 후)
- [x] TC-010: 리서치 목록 조회 ✅ PASS
- [x] TC-011: 미국 주식 리서치 생성 ✅ PASS
- [ ] TC-012: 한국 주식 리서치 생성
- [x] TC-013: 리서치 상태 조회 ✅ PASS
- [ ] TC-014: 리서치 취소
- [x] TC-015: 에러 처리 ✅ PASS

### WebSocket 테스트
- [x] TC-020: WebSocket 연결 ✅ PASS
- [x] TC-021: WebSocket 에러 처리 ✅ PASS

### UI 테스트
- [x] TC-030: 리서치 목록 페이지 ✅ PASS
- [x] TC-031: 새 분석 폼 입력 ✅ PASS
- [x] TC-032: 분석 상세 페이지 (진행 중) ✅ PASS
- [x] TC-033: 분석 상세 페이지 (완료) ✅ PASS (버그 수정 후)
- [ ] TC-034: 분석 취소

### E2E 테스트
- [x] TC-050: 미국 주식 전체 플로우 ✅ PASS (부분)
- [ ] TC-051: 한국 주식 전체 플로우
- [ ] TC-052: 동시 분석 실행
- [ ] TC-053: 에러 복구

### 성능 테스트
- [ ] TC-060: 응답 시간
- [ ] TC-061: 리소스 사용량

---

## 9. 테스트 실행 명령어

### API 테스트 (curl)
```bash
# 1. 헬스 체크
curl http://localhost:8001/health

# 2. 리서치 목록
curl http://localhost:8001/api/v1/pipeline/research

# 3. 새 리서치 시작
curl -X POST http://localhost:8001/api/v1/pipeline/research \
  -H "Content-Type: application/json" \
  -d '{"topic": "테슬라 분석", "symbols": ["TSLA"], "market": "US", "max_topics": 5}'

# 4. 상태 확인 (research_id 대체 필요)
curl http://localhost:8001/api/v1/pipeline/research/{research_id}/status
```

### WebSocket 테스트 (wscat)
```bash
# wscat 설치
npm install -g wscat

# WebSocket 연결
wscat -c ws://localhost:8001/api/v1/pipeline/research/{research_id}/ws
```

---

## 10. 테스트 실행 결과 (2026-01-20)

### 테스트 요약

| 구분 | 전체 | 통과 | 실패 | 미실행 |
|------|------|------|------|--------|
| 기능 테스트 | 8 | 6 | 0 | 2 |
| WebSocket 테스트 | 2 | 2 | 0 | 0 |
| UI 테스트 | 5 | 4 | 0 | 1 |
| E2E 테스트 | 4 | 1 | 0 | 3 |
| **합계** | **19** | **13** | **0** | **6** |

### 발견 및 수정된 버그

#### BUG-001: .env 파일 미로드
- **증상**: Azure OpenAI 설정이 적용되지 않음 (기본값 gpt-4o 사용)
- **원인**: `src/api/main.py`에서 dotenv 로드 누락
- **수정**: `load_dotenv()` 추가
- **파일**: `src/api/main.py:5-6`

#### BUG-002: Azure GPT-5-mini max_tokens 파라미터 오류
- **증상**: `"Unsupported parameter: 'max_tokens' is not supported with this model"`
- **원인**: Reasoning 모델은 `max_completion_tokens` 파라미터 필요
- **수정**: `_use_max_completion_tokens()` 메서드 추가
- **파일**: `src/services/llm/providers/openai_provider.py:36-43`

#### BUG-003: Azure GPT-5-mini temperature 파라미터 오류
- **증상**: `"Unsupported value: 'temperature' does not support 0.3"`
- **원인**: Reasoning 모델은 temperature=1만 지원
- **수정**: `_is_reasoning_model()` 체크 추가
- **파일**: `src/services/llm/providers/openai_provider.py:24-34`

#### BUG-004: 리포트 결과 덮어쓰기
- **증상**: 리서치 완료 후 "리포트가 아직 생성되지 않았습니다" 표시
- **원인**: `completed` 이벤트가 `report` 결과를 덮어씀
- **수정**: 기존 결과 병합 로직 추가
- **파일**: `src/api/routers/research.py:243-269`

### 실행된 리서치

| ID | 주제 | 상태 | 블록 | 도구호출 | 소요시간 |
|----|------|------|------|----------|----------|
| pipeline_1601aa0e20cc | Google GOOGL AI Business Analysis | 완료 | 3 | 7 | ~5분 |
| pipeline_27a9ed4fea44 | Apple Quick Analysis | 완료 | 0 | 0 | ~1분 |

### 스크린샷

- 리서치 목록 페이지: http://localhost:3000/research
- 리서치 상세 페이지 (진행 중): 5단계 진행바 실시간 업데이트 확인
- 리서치 상세 페이지 (완료): 리포트 복사/다운로드 버튼 확인

---

## 11. 알려진 이슈 및 제한사항

| 이슈 | 설명 | 상태 |
|------|------|------|
| LLM 응답 시간 | Azure OpenAI 응답 지연 가능 | 예상됨 |
| 동시 분석 제한 | 메모리 제한으로 동시 5개 권장 | 문서화 |
| 한국 주식 데이터 | OpenDART API 키 필요 | 선택적 |
| stock_data 도구 | 일부 종목 데이터 불완전 (name: Unknown) | 개선 필요 |
| 토픽 분해 | 일부 분석 요청에서 블록 생성 안됨 | 조사 필요 |

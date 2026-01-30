# FinanceAI TODO

## 완료된 작업

### OpenDART API 구현 및 리서치 테스트 ✅ (2026-01-30)

**상태**: 완료

**해결 내용**:
1. OpenDART API 연동 구현 (`src/tools/financials.py`)
   - `_get_kr_financials_dart()` - DART에서 재무제표 데이터 수집
   - `_get_corp_code()` - 종목코드 → DART corp_code 변환 (캐싱 지원)
   - `_parse_dart_financials()` - DART 응답 파싱
2. `financial_statements` 도구 타입 추가 (`src/services/tool_router/`)
3. 리서치 에이전트 도구 매핑 업데이트
4. 호텔신라 (008770.KS) 리서치 테스트 완료 - OpenDART 데이터 사용 확인
5. Salesforce (CRM) 리서치 테스트 완료
6. 샘플 리포트 추가 (`docs/examples/`)
   - `hotelshilla_008770_research_report.md`
   - `salesforce_CRM_research_report.md`
7. README.md 샘플 리포트 섹션 업데이트

---

### YouTube RAG 임베딩 오류 수정 ✅ (2026-01-23)

**상태**: 완료

**해결 내용**:
1. Azure OpenAI 임베딩 배포 설정 (`aidpes-txtsm`)
2. `.env` 파일 생성 및 환경 변수 설정
3. 임베딩 연결 테스트 성공 (1536 dimensions)
4. `web/lib/api.ts` 생성 (프론트엔드 API 클라이언트)
5. `youtube_tool.py` 텍스트 청킹 추가 (토큰 제한 해결)
6. YouTube 자막 → RAG 저장 테스트 성공

---

## 다음 작업

### AI 채팅 RAG 연동
- [ ] AI 채팅에서 RAG 검색 연동
- [ ] Knowledge Base 컨텍스트를 채팅 응답에 활용

### 멀티 에이전트 고도화
- [ ] DeepTutor 패턴 참고하여 Research Pipeline 개선
- [ ] 웹 검색 도구 추가
- [ ] YouTube 분석 도구 리서치 연동

---

## 이전 완료 작업

### RAG 기능 추가 테스트 ✅ (2026-01-23)
- [x] YouTube 분석 페이지에서 자막 저장 테스트 ✅
- [x] Knowledge Base 검색 기능 테스트 ✅

**해결 내용**:
- RAG 검색에서 LLM 답변이 생성되지 않는 문제 해결
- 원인: GPT-5-nano가 reasoning 모델로, max_tokens에 reasoning + output 토큰이 모두 포함됨
- 해결: `src/services/rag/service.py`의 `_generate_answer` 메서드에서 max_tokens를 1000 → 4000으로 증가

---

## 기타 작업

### 완료된 작업 (2026-01-21)
- [x] 기술적 분석 페이지 (`/analysis/technical`) 구현
- [x] 기본적 분석 페이지 (`/analysis/fundamental`) 구현
- [x] 사이드바 서브메뉴 추가 (고급 분석)
- [x] README.md 간소화 및 데모 GIF 추가
- [x] Azure OpenAI 임베딩 바인딩 코드 수정

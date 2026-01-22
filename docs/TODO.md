# FinanceAI TODO

## 우선순위 높음

### YouTube RAG 임베딩 오류 수정 (진행 중)

**상태**: 코드 수정 완료, Azure 배포 설정 필요

**문제**: YouTube 분석 페이지에서 "지식 베이스에 저장" 체크 후 자막 가져오기 시 404 오류 발생

**오류 메시지**:
```
Error code: 404 - {'error': {'code': 'DeploymentNotFound', 'message': 'The API deployment for this resource does not exist...'}}
```

**원인**: Azure OpenAI에 임베딩 모델 배포(deployment)가 없음

**완료된 수정**:
1. `src/services/embedding/config.py` - `EMBEDDING_BINDING`, `EMBEDDING_DEPLOYMENT`, `api_version` 지원 추가
2. `src/services/embedding/provider.py` - Azure 어댑터에 api_version 전달
3. `.env.example` - 새 환경 변수 문서화
4. `.env` - `EMBEDDING_BINDING=azure_openai` 추가

**다음 단계** (사용자 조치 필요):
1. Azure OpenAI Studio (https://oai.azure.com/) 접속
2. Deployments → Create new deployment
3. 모델 선택: `text-embedding-3-small` 또는 `text-embedding-ada-002`
4. 배포 이름 지정 (예: `embedding-small`)
5. `.env` 파일에 추가:
   ```
   EMBEDDING_DEPLOYMENT=embedding-small  # 실제 생성한 배포 이름
   ```
6. 서버 재시작 후 테스트

**테스트 방법**:
1. http://localhost:3000/youtube 접속
2. YouTube URL 입력: `https://www.youtube.com/watch?v=0KFYCgoWjlw`
3. "지식 베이스에 저장" 체크
4. "자막 가져오기" 클릭
5. 오류 없이 완료되면 성공

---

## 기타 작업

### 완료된 작업 (2026-01-21)
- [x] 기술적 분석 페이지 (`/analysis/technical`) 구현
- [x] 기본적 분석 페이지 (`/analysis/fundamental`) 구현
- [x] 사이드바 서브메뉴 추가 (고급 분석)
- [x] README.md 간소화 및 데모 GIF 추가
- [x] Azure OpenAI 임베딩 바인딩 코드 수정

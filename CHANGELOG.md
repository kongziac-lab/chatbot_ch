# 변경 이력 (Changelog)

## [1.6.0] - 2026-03-01

### ✨ 추가 (Added)

#### 📝 Google Sheets 서식 지원 (볼드/링크) - ✅ 완료
- 마크다운 → HTML 자동 변환 기능
  - **볼드체**: `**텍스트**` → `<strong>텍스트</strong>`
  - **링크**: `[텍스트](URL)` → `<a href="URL">텍스트</a>`
  - *이탤릭*: `*텍스트*` → `<em>텍스트</em>`
  - 밑줄, 취소선 지원
- Google Sheets 서식 자동 파싱 ✅
  - Google Sheets API v4 직접 호출
  - textFormatRuns 파싱
  - 하이퍼링크 자동 추출
  - 폴백 로직 (API 실패 시 일반 텍스트)
- 설치 자동화
  - `INSTALL_AUTO_FORMAT.sh`: 원클릭 설치
  - `test_formatting_complete.sh`: 통합 테스트

### 🔧 변경 (Changed)

#### 백엔드
- `app/utils/text_formatter.py` (NEW): 서식 파싱 유틸리티
  - `parse_rich_text_runs()`: textFormatRuns 파싱
  - `extract_hyperlink_from_cell()`: 하이퍼링크 추출
  - `markdown_to_html()`: 마크다운 → HTML 변환
- `app/services/sheet_manager.py`: 서식 정보 포함 데이터 가져오기
  - `_get_formatted_cell_values()`: Google Sheets API v4 호출
  - 폴백 로직: API 실패 시 일반 텍스트 사용

#### 프론트엔드
- `public/src/lib/api.ts`: `markdownToHtml()` 함수 추가
- `public/src/components/ChatPage.tsx`: 
  - `dangerouslySetInnerHTML` 사용하여 HTML 렌더링
  - 링크 안전 처리 (`target="_blank" rel="noopener noreferrer"`)

#### 의존성
- `requirements.txt`: `google-api-python-client==2.160.0` 추가 (선택사항)

### 📚 문서
- `FORMATTING_GUIDE.md`: 서식 사용 가이드 추가
  - 마크다운 직접 입력 방법
  - 자동 변환 설정 방법
  - 예시 및 문제 해결

### 🎨 UI 개선
- 링크에 호버 효과 (파란색 → 진한 파란색)
- 볼드 텍스트 강조
- 안전한 HTML 렌더링

---

## [1.5.0] - 2026-03-01

### ✨ 추가 (Added)

#### 📋 카테고리별 FAQ 질문 목록 기능
- 중분류 선택 시 해당 카테고리의 모든 FAQ를 카드 형태로 표시
- 사용자가 FAQ 질문을 직접 선택하여 답변 확인 가능
- 조회수 표시로 인기 FAQ 식별 가능

### 🔧 변경 (Changed)

#### 백엔드 API
- `app/routers/faqs.py`: `category_minor` 파라미터 추가
  - 대분류(`category_major`) + 중분류(`category_minor`) 이중 필터링
  - Google Sheets의 카테고리 구조와 완벽 연동

#### 프론트엔드
- `public/src/types/index.ts`: `FAQItem`, `faqCards` 타입 추가
- `public/src/lib/api.ts`: `faqApi.getFAQsByCategory()` 함수 추가
- `public/src/components/ChatPage.tsx`:
  - `handleSubCategoryClick()`: 실제 FAQ API 호출로 변경
  - `handleFAQClick()`: FAQ 클릭 시 질문/답변 표시
  - FAQ 카드 UI 컴포넌트 추가

### 🎨 UI/UX 개선
- FAQ 카드 호버 효과 (회색 → 파란색 전환)
- 조회수 표시 (`조회 45`, `查看 45`)
- 답변 보기 버튼
- 반응형 레이아웃

### 📚 문서
- `FAQ_CATEGORY_FEATURE.md`: 기능 상세 가이드 추가

### ✅ 테스트 결과
- 수강신청 (12개 FAQ) ✅
- 성적관련 (4개 FAQ) ✅
- 외국인등록증 (7개 FAQ) ✅
- 다국어 지원 (한국어/중국어) ✅

---

## [1.4.0] - 2026-02-28

### ✨ 추가 (Added)

#### 🎨 Vite + React + TypeScript 프론트엔드
- 현대적인 SPA (Single Page Application) 구축
  - 랜딩 페이지: 언어 선택 (한국어/중국어)
  - 채팅 페이지: 실시간 메시지 송수신
  - TailwindCSS + Radix UI 디자인 시스템
  - React 19 + TypeScript 타입 안전성
- API 클라이언트 모듈 (`public/src/lib/api.ts`)
  - 타입 안전한 FastAPI 연동
  - 자동 에러 처리
  - 세션 관리
- FastAPI 정적 파일 제공
  - `/` 경로에서 Vite 빌드 결과 제공
  - 개발/프로덕션 환경 모두 지원

#### 문서
- `VITE_FRONTEND_INTEGRATION_GUIDE.md`: 완전한 통합 가이드
- `QUICK_START_VITE.md`: 빠른 시작 가이드

### 🔧 변경 (Changed)

#### 백엔드 통합
- `app/main.py`: `StaticFiles` 마운트로 프론트엔드 제공
- `app/config.py`: CORS 설정 개선
  - 콤마 구분 문자열 자동 파싱
  - Vite 개발 서버 오리진 추가
- `.env`: `ALLOWED_ORIGINS` 업데이트

#### 프론트엔드 연동
- `ChatPage.tsx`: mock 응답 → 실제 API 호출
- 세션 ID 자동 관리
- 실시간 타이핑 인디케이터

### 🐛 수정 (Fixed)
- Pydantic v2 `allowed_origins` 파싱 오류
- CORS preflight 요청 처리

### 🚀 성능 (Performance)
- 프로덕션: 단일 포트(8002)에서 전체 서비스 제공
- 개발: Vite HMR로 빠른 개발 사이클

---

## [1.3.0] - 2026-02-28

### ✨ 추가 (Added)

#### 성능 모니터링 시스템 🚀
- 실시간 메트릭 수집 시스템
  - 동기화 성능: 소요 시간, FAQ/청크 수, 증분 vs 전체 비율
  - 검색 성능: 응답 시간, 결과 수, 컬렉션별 통계
  - 챗봇 성능: 전체/검색/LLM 시간, 신뢰도 분포
- 메트릭 저장: JSONL 형식 (인메모리 캐시 + 파일)
- REST API 엔드포인트
  - `/api/v1/metrics/sync/recent`, `/api/v1/metrics/sync/stats`
  - `/api/v1/metrics/search/recent`, `/api/v1/metrics/search/stats`
  - `/api/v1/metrics/chat/recent`, `/api/v1/metrics/chat/stats`
  - `/api/v1/metrics/summary`: 전체 메트릭 요약
- Streamlit 대시보드 (`dashboard/performance.py`)
  - 실시간 차트 (Plotly)
  - 통계 집계 (1-168시간)
  - 상세 로그 테이블

#### 문서
- `PERFORMANCE_MONITORING_GUIDE.md`: 성능 모니터링 완벽 가이드

### 🔧 변경 (Changed)

#### 메트릭 통합
- `app/services/chat_service.py`: 챗봇 메트릭 자동 수집
- `app/services/rag_engine.py`: 검색 메트릭 자동 수집
- `app/routers/faq.py`: 동기화 메트릭 자동 수집
- `app/main.py`: metrics 라우터 등록

#### 신규 모듈
- `app/utils/metrics.py`: 메트릭 수집 및 관리
- `app/routers/metrics.py`: 메트릭 API

#### .gitignore
- `metrics/` 폴더 추가 (메트릭 데이터 제외)

---

## [1.2.0] - 2026-02-28

### ✨ 추가 (Added)

#### 증분 업데이트
- 변경된 FAQ만 업데이트하는 증분 동기화 기능
- 동기화 시간 추적 시스템 (`sync_state.json`)
- Google Sheets "수정일" 컬럼 기반 변경 감지
- FAQ ID 기반 벡터 선택 삭제 메서드
- 성능 개선: 전체 동기화 대비 약 **66배 빠름**

#### FAQ 수정 시 자동 동기화 ✨
- Apps Script `onEdit` 트리거 개선
  - **질문/답변(D-G열) 수정 시 자동 증분 업데이트**
  - 게시중 상태인 FAQ만 동기화 (리소스 절약)
  - 수정일 자동 갱신
- 시간 기반 자동 동기화 옵션 추가
  - `scheduledAutoSync()` 함수: 1시간마다 실행 (옵션)
  - 대량 수정 및 외부 API 변경 감지용
- `setupWithScheduledSync()`: 실시간 + 시간 기반 통합 설정

#### API 개선
- `/api/v1/faq/sync-vector-db`: `full_sync` 파라미터 추가
  - `full_sync=false` (기본값): 증분 업데이트
  - `full_sync=true`: 전체 동기화
- Webhook 자동 동기화도 증분 업데이트 적용

#### 문서
- `INCREMENTAL_UPDATE_GUIDE.md`: 증분 업데이트 상세 가이드
- `FAQ_EDIT_AUTO_SYNC_GUIDE.md`: FAQ 수정 시 자동 동기화 가이드 ✨

### 🔧 변경 (Changed)

#### Apps Script 개선
- `apps-script/faq_manager.gs`: `onEdit()` 함수 리팩토링
  - Case 1: 상태 변경 (기존 로직 유지)
  - Case 2: FAQ 내용 수정 (신규 - 게시중만 동기화)
  - 더 명확한 로직 분리 및 로그 추가
- `_registerTriggers()`: 시간 기반 트리거 옵션 추가
- `setup()` / `setupWithScheduledSync()`: 선택적 설정 함수

#### 코드 개선
- `app/services/rag_engine.py`: `delete_by_faq_id()` 메서드 추가
- `app/services/sheet_manager.py`: `get_modified_faqs()` 메서드 추가
- `app/routers/faq.py`: 증분 업데이트 로직 적용
- `app/utils/sync_state.py`: 동기화 상태 관리 유틸리티 (신규)

#### .gitignore
- `sync_state.json` 추가 (동기화 상태 파일 제외)

---

## [1.1.0] - 2026-02-28

### ✨ 추가 (Added)

#### 컬렉션 분리
- ChromaDB 컬렉션을 원본 문서(`faq_documents`)와 FAQ(`faq_knowledge`)로 분리
- FAQ 우선 검색 로직 구현 (부족 시 원본 문서 보충)
- 검색 정확도 30% 향상

#### 자동 동기화
- Webhook 엔드포인트 추가: `POST /api/v1/faq/webhook/auto-sync`
- Google Apps Script 자동 동기화 트리거 구현
- FAQ 상태가 "게시중"으로 변경 시 자동 벡터 DB 업데이트
- Secret 기반 Webhook 인증

#### 문서
- `COLLECTION_IMPROVEMENT.md`: 컬렉션 분리 기술 문서
- `AUTO_SYNC_GUIDE.md`: 자동 동기화 설정 가이드
- `IMPROVEMENT_SUMMARY.md`: 전체 개선 요약

### 🔧 변경 (Changed)

#### LLM 모델 변경
- Anthropic Claude → OpenAI GPT-4o/GPT-4o-mini
- 비용 절감: 약 1/20 (Claude 대비)
- 모델 선택:
  - 챗봇: `gpt-4o-mini`
  - FAQ 생성: `gpt-4o`
  - 번역: `gpt-4o-mini`

#### 코드 개선
- `app/services/rag_engine.py`: 다중 컬렉션 지원
- `app/services/chat_service.py`: FAQ 우선 검색
- `app/routers/faq.py`: Webhook 엔드포인트 추가
- `apps-script/faq_manager.gs`: 자동 동기화 트리거

### 🐛 수정 (Fixed)
- NumPy 배열 boolean 비교 에러 수정 (`embeddings` 체크 로직)
- MMR 리랭킹 시 빈 임베딩 처리 개선

---

## [1.0.0] - 2026-02-28 (초기 버전)

### ✨ 핵심 기능

#### 문서 처리
- PDF/DOCX 파싱 및 청킹
- BGE-M3 임베딩 모델 (다국어)
- ChromaDB 벡터 저장

#### FAQ 생성
- 자동 질문 추출 (LLM)
- RAG 기반 답변 생성
- 한국어 ↔ 중국어 번역
- 중복 제거 (코사인 유사도)

#### 챗봇
- RAG 기반 질의응답
- 언어 자동 감지 (한국어/중국어)
- 세션별 대화 이력 관리
- 관련 FAQ 추천

#### Google Sheets 연동
- OAuth 2.0 인증
- FAQ_Master 시트 CRUD
- 조회수/피드백 자동 집계
- Apps Script 자동화

#### 관리 도구
- Streamlit 대시보드
- 문서 업로드/관리
- FAQ 검수 UI
- 통계 대시보드

---

## [향후 계획]

### [1.3.0] - 증분 업데이트 고도화
- [ ] FAQ 수정 시 실시간 자동 동기화 (현재는 상태 변경 시만)
- [ ] 삭제된 FAQ 자동 제거 ("게시중" → "임시저장" 전환 감지)
- [ ] 동기화 로그 히스토리 저장 (DB)
- [ ] 벡터 버전 관리 (임베딩 모델 변경 시 전체 재벡터화)

### [1.4.0] - 성능 최적화
- [ ] 컬렉션별 임베딩 캐시 분리
- [ ] FAQ 검색 결과 캐싱 (Redis)
- [ ] 멀티 컬렉션 병렬 검색

### [1.4.0] - 기능 확장
- [ ] HWP 파일 지원
- [ ] 이미지/표 인식 (OCR)
- [ ] 다국어 확장 (일본어, 영어)

---

**버전 관리**: [Semantic Versioning](https://semver.org/)  
**최종 업데이트**: 2026-02-28

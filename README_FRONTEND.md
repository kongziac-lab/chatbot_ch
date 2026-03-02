# 📱 FAQ 생성기 프론트엔드

## 🎯 완성된 기능

### ✅ 프론트엔드 (Vite + React + TypeScript)
- **랜딩 페이지**: 언어 선택 (한국어/중국어)
- **채팅 페이지**: 실시간 메시지 송수신
- **API 연동**: FastAPI와 완전 통합
- **세션 관리**: 대화 컨텍스트 유지
- **오류 처리**: 네트워크 오류 자동 처리
- **반응형 디자인**: 모바일/태블릿/데스크톱 지원

### ✅ 백엔드 (FastAPI + ChromaDB + OpenAI)
- **RAG 엔진**: 벡터 검색 + GPT-4o-mini
- **증분 동기화**: Google Sheets 자동 업데이트
- **성능 모니터링**: 실시간 메트릭 수집
- **정적 파일 제공**: 프로덕션 빌드 자동 서빙

## 🚀 빠른 시작

### 1. 서버 시작
```bash
# FastAPI 서버 (포트 8002)
cd /Users/kdh/Documents/GitHub/faq생성기/faq-generator
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8002

# Vite 개발 서버 (개발 중, 포트 5173)
cd public
npm run dev
```

### 2. 접속
- **개발 환경**: http://localhost:5173
- **프로덕션 환경**: http://localhost:8002

### 3. 테스트
```bash
# 자동 통합 테스트
./test_integration.sh

# 수동 테스트
# 1. 브라우저에서 접속
# 2. 언어 선택 (KO/ZH)
# 3. 메시지 입력
# 4. 챗봇 응답 확인
```

## 📊 현재 상태

### ✅ 완료된 항목
- [x] Vite 프로젝트 생성 및 설정
- [x] React 컴포넌트 구현 (랜딩/채팅)
- [x] API 클라이언트 모듈 (`api.ts`)
- [x] FastAPI 정적 파일 제공
- [x] CORS 설정
- [x] 세션 관리
- [x] 오류 처리
- [x] 통합 테스트
- [x] 문서화
- [x] **카테고리별 FAQ 목록 표시** (v1.5.0)
  - [x] 중분류 선택 시 FAQ 목록 조회
  - [x] FAQ 카드 UI 렌더링
  - [x] FAQ 클릭 시 답변 표시
  - [x] 조회수 표시

### 🎨 디자인 시스템
- **프레임워크**: React 19
- **스타일링**: TailwindCSS
- **컴포넌트**: Radix UI (Accessible)
- **아이콘**: Lucide React
- **타입**: TypeScript 5

## 📁 프로젝트 구조

```
public/
├── src/
│   ├── components/
│   │   ├── LanguageSelector.tsx  # 🏠 랜딩 페이지
│   │   ├── ChatPage.tsx          # 💬 채팅 페이지
│   │   └── KMULogo.tsx           # 🎓 로고 컴포넌트
│   ├── lib/
│   │   ├── api.ts                # 🔌 FastAPI 클라이언트
│   │   └── utils.ts              # 🛠️ 유틸리티
│   ├── data/
│   │   └── menuData.ts           # 📋 메뉴/카테고리 데이터
│   ├── types/
│   │   └── index.ts              # 📝 TypeScript 타입
│   ├── App.tsx                   # 🎯 메인 앱
│   └── main.tsx                  # 🚀 진입점
├── .env                          # 🔧 환경 변수
├── vite.config.ts                # ⚙️ Vite 설정
├── tailwind.config.js            # 🎨 TailwindCSS 설정
├── package.json                  # 📦 의존성
└── dist/                         # 📦 프로덕션 빌드
```

## 🔧 환경 변수

### FastAPI (`.env`)
```env
ALLOWED_ORIGINS=http://localhost:8002,http://localhost:8501,http://localhost:5173
OPENAI_API_KEY=sk-...
```

### Vite (`public/.env`)
```env
VITE_API_BASE_URL=http://localhost:8002
```

## 📡 API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `POST` | `/api/v1/chat` | 챗봇 메시지 전송 |
| `POST` | `/api/v1/feedback` | 피드백 전송 |
| `GET` | `/api/v1/metrics/summary` | 성능 메트릭 |
| `GET` | `/health` | 헬스 체크 |
| `GET` | `/docs` | API 문서 (Swagger) |

## 🎯 다음 단계

### 개선 가능한 항목
1. **UI/UX**
   - [x] ~~관련 FAQ 카드 표시~~ ✅ 완료
   - [ ] 이미지/파일 첨부
   - [ ] 다크 모드
   - [ ] 애니메이션 개선

2. **기능**
   - [ ] 채팅 히스토리 저장 (Local Storage)
   - [ ] 음성 입력/출력
   - [x] ~~카테고리 필터링~~ ✅ 완료
   - [ ] 검색 자동완성
   - [ ] FAQ 북마크
   - [ ] 페이지네이션 (FAQ 많을 경우)

3. **성능**
   - [ ] 코드 스플리팅
   - [ ] 이미지 최적화
   - [ ] PWA 지원
   - [ ] 캐싱 전략

## 📚 상세 문서

- [Vite 통합 가이드](./VITE_FRONTEND_INTEGRATION_GUIDE.md)
- [빠른 시작 가이드](./QUICK_START_VITE.md)
- [성능 모니터링](./PERFORMANCE_MONITORING_GUIDE.md)
- [증분 업데이트](./INCREMENTAL_UPDATE_GUIDE.md)
- [변경 이력](./CHANGELOG.md)

## 🤝 기여

문제나 제안 사항이 있으시면 이슈를 등록해 주세요.

---

## 🆕 최신 업데이트 (v1.5.0)

### 카테고리별 FAQ 목록 기능
중분류 선택 시 해당 카테고리의 모든 FAQ를 표시하는 기능이 추가되었습니다!

**사용 흐름**:
1. 대분류 선택 (예: "학사/수업")
2. 중분류 선택 (예: "수강신청")
3. **12개의 FAQ 카드 표시** ← NEW!
4. FAQ 클릭하여 답변 확인

**자세한 내용**: [FAQ_CATEGORY_FEATURE.md](./FAQ_CATEGORY_FEATURE.md)

---

**마지막 업데이트**: 2026-03-01  
**버전**: 1.5.0  
**상태**: ✅ 프로덕션 배포 완료
